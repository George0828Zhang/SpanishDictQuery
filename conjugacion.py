import requests
import sys
import csv
import re
import os
import argparse

from bs4 import BeautifulSoup
from tabulate import tabulate

class VerbQuery:
    def __init__(self):
        self.base_url = "https://www.spanishdict.com/conjugate/"
        self.tenses = [
        'presentIndicative',
        'preteritIndicative',
        'imperfectIndicative',
        'imperative',
        'presentParticiple',
        'pastParticiple',
        # 'negativeImperative'
        ]


    def query(self, verbo):
        url = self.base_url + verbo
        page = requests.get(url)
        assert page.status_code == 200
        soup = BeautifulSoup(page.text, 'html.parser')
        
        x = soup.find_all("a", class_='sd-track-click vtable-word-text')        

        result = {}
        for t in self.tenses:
            result[t] = [""]*6
        for c in x:
            p = int(c.attrs['data-person'])
            t = c.attrs['data-tense']
            v_ = c.text
            ####################
            if t=="imperative" and p==3:
                continue
            ####################
            if t in self.tenses:
                result[t][p] = v_

        y = soup.find_all(class_="conj-basic-word")
        for c in y:
            t = c.attrs['data-tense']
            v_ = c.text
            if t in self.tenses:
                result[t][0] = v_

        pattern = r'"quickdef1":{"displayText":"(?P<definition>.+?)"'
        result["def"] = re.search(pattern, page.text).group("definition")

        head = soup.find("div", class_='headwordDesktop--2XpdH')
        result["head"] = head.text
        return self.regularity(result)

    @staticmethod
    def regularity(conju):
        template = {
            "ar": {
                "presentIndicative": ['o', 'as', 'a', 'amos', 'áis', 'an'],
                "preteritIndicative": ['é', 'aste', 'ó', 'amos', 'asteis', 'aron'],
                "imperfectIndicative": ['aba', 'abas', 'aba', 'ábamos', 'abais', 'aban'],           
                "imperative": ['','a','e','','ad','en'],
                "presentParticiple": ['ando'],
                "pastParticiple": ['ado'],
                },
            "er": {
                "presentIndicative": ['o', 'es', 'e', 'emos', 'éis', 'en'],
                "preteritIndicative": ['í', 'iste', 'ió', 'imos', 'isteis', 'ieron'],
                "imperfectIndicative": ['ía', 'ías', 'ía', 'íamos', 'íais', 'ían'],         
                "imperative": ['','e','a','','ed','an'],
                "presentParticiple": ['iendo'],
                "pastParticiple": ['ido'],
                },
            "ir": {
                "presentIndicative": ['o', 'es', 'e', 'imos', 'ís', 'en'],
                "preteritIndicative": ['í', 'iste', 'ió', 'imos', 'isteis', 'ieron'],
                "imperfectIndicative": ['ía', 'ías', 'ía', 'íamos', 'íais', 'ían'],         
                "imperative": ['','e','a','','id','an'],
                "presentParticiple": ['iendo'],
                "pastParticiple": ['ido'],
                },
            
        }
        pn_reflex = ['me', 'te', 'se', 'nos', 'os', 'se']

        verbo = conju['head']

        # reflexive = verbo[-2:] == "se"        
        # if reflexive:
        #     root = verbo[:-4]
        #     tail = verbo[-4:-2]
        # else:
        #     root = verbo[:-2]
        #     tail = verbo[-2:]
        root = verbo[:-2]
        tail = verbo[-2:]
        tail = tail.replace('ír', 'ir')
        form = template[tail]
        for tense, suffix in form.items():
            irr = False
            for p in range(6):
                if conju[tense][p] == "" or suffix[p] == "":
                    continue
                pattern = "({0}{1})|({2} {0}{1})|({0}{1}{2})".format(root, suffix[p], pn_reflex[p])
                if re.match(pattern, conju[tense][p]) is None:                    
                    irr = True
                    break

            conju[tense].insert(0, "irregular" if irr else "regular")
        return conju

def visualize(result):
    processed = [[""]*len(fieldnames) for i in range(6)]
    processed[0][0] = result['head']
    processed[1][0] = result['def']
    for i,t in enumerate(Q.tenses):
        processed[0][i*2+1] = result[t][0]
        for p in range(6):
            processed[p][i*2+2] = result[t][p+1]
    return processed    

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--list", "-l", default="",
        type=str, help="path to list file.")   
    parser.add_argument("--out", "-o", default="formatted.csv",
        type=str, help="path to output file.") 
    parser.add_argument("--shell", "-s", action='store_true',
                        help="Run shell mode.")
    args = parser.parse_args()

    Q = VerbQuery()

    fieldnames = [
    "Verb",
    "","present",
    "","preterit",
    "","imperfect",
    "","imperative",
    "","progressive",
    "","p.p."]
    

    if os.path.isfile(args.list):
        table = []
        with open(args.list, "r", encoding="utf-8") as f:
            verbos = []
            for line in f:
                v = line.strip().lower()
                verbos.append(v)

            for v in sorted(verbos):
                result = Q.query(v)
                processed = visualize(result)
                print(tabulate(processed))
                table.extend(processed)

        with open(args.out, "w", encoding="utf-8", newline='') as f:
            writer = csv.writer(f)
            writer.writerow(fieldnames)
            for row in table:
                writer.writerow(row)
    else:        
        EXIT = ("exit", "quit", "q")
        v = input("Entra un verbo:").lower()
        while v not in EXIT:
            result = Q.query(v)
            processed = visualize(result)
            processed = [fieldnames] + processed
            print(tabulate(processed))
            v = input("Entra un verbo:").lower()


