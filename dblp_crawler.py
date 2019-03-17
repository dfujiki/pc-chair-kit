# -*- coding: utf-8 -*-
import urllib.request
import xmltodict
from time import sleep
from tqdm import tqdm
from os import remove, rename
from os.path import exists
import os.path
from util import read_csv, write_csv, copy_dic
import unidecode
import html
import argparse
import pickle
from multiprocessing import Pool, Lock, cpu_count

#--------------------
# Hack urlopen
#--------------------
import socket
origGetAddrInfo = socket.getaddrinfo

def getAddrInfoWrapper(host, port, family=0, socktype=0, proto=0, flags=0):
    return origGetAddrInfo(host, port, socket.AF_INET, socktype, proto, flags)

# replace the original socket.getaddrinfo by our version
socket.getaddrinfo = getAddrInfoWrapper

def sanitize_text(text):
    text = unidecode.unidecode(html.unescape(text.decode('ascii')))
    return text.replace("&", " ")

lock = Lock()

class Cache(object):
    def __init__(self, path='data/.cache_queries'):
        self.backup_ctr = 0
        self.path = path
        self.queries = {}

    def backup(self):
        if os.path.exists(self.path):
            backupname = self.path + ".bak"
            if os.path.exists(backupname):
                os.remove(backupname)
            os.rename(self.path, backupname)

    def backup_and_save(self, force=False):
        self.backup_ctr += 1
        if self.backup_ctr % 100 == 0 or force:
            self.backup()
            with  open(self.path, "wb") as f:
                pickle.dump(self, f, -1)

    @classmethod
    def load(cls, path):
        if os.path.exists(path):
            try:
                with open(path, "rb") as f:
                    cache = pickle.load(f, errors="strict")
                return cache
            except Exception as ex:
                print("Problem loading paper cache, with exception",
                      ex.__class__.__name__,
                      "if this persists, re-create %s" % path)
                raise ex

        else:
            print("Cache not found, creating")
            return cls(path)

    def __contains__(self, key):
        return key in self.queries

    def add_query(self, key, response):
        if key not in self.queries:
            self.queries[key] = response

    def get_query(self, key):
        if key in self.queries:
            return self.queries[key]
        else:
            return None


# This is needed to make sure cache instance is attributed to dblp_crawler module, not __main__
if __name__ == "__main__":
    from dblp_crawler import Cache
cache = Cache.load('data/.cache_queries')

def save_cache():
    cache.backup_and_save(True)


def request_dblp(query):
    url = ('http://dblp.uni-trier.de/%s' % query)

    num_retries = 2
    while num_retries > 0:
        try:
            if query in cache:
                raw_str = cache.get_query(query)
            else:
                resource = urllib.request.urlopen(url)
                raw_str = resource.read()
                lock.acquire()
                cache.add_query(query, raw_str)
                cache.backup_and_save()
                lock.release()

            raw_str = sanitize_text(raw_str)
            return xmltodict.parse(raw_str)

        except urllib.error.HTTPError as err:
            if err.code == 429:
                print("HTTP error code", err.code, "reason:", err.reason, "will wait:", err.headers['Retry-After'])
                wait = int(err.headers['Retry-After'])
                sleep(wait + 10)
                num_retries -= 1
            else:
                raise err
        except Exception as err:
            print("Something bad happend:", str(err))
            print(raw_str)
            raise err

    # woops we failed
    raise Exception("Something wrong happened, we run out of tries")


def request_author_key(author):
    data = request_dblp('search/author?xauthor="%s"' %
                        author.replace(' ', '+'))
    # TODO DOES NOT WORK IF THE PERSON HAS ALIASES
    if not data['authors']:
        return ['']
    elif isinstance(data['authors']['author'], list):
        return [a['@urlpt'] for a in data['authors']['author']]
    else:
        return [data['authors']['author']['@urlpt']]


def make_author_link(key):
    return "http://dblp.uni-trier.de/pers/hd/" + key


def request_publication_keys(author_key):
    data = request_dblp('rec/pers/%s/xk' %
                        author_key)
    return data['dblpperson']['dblpkey'][1:]


def sanitize_coauthors(authors):
    sanitized_authors = []
    # Check if we have a bunch of letters as authors:
    bad_authors = True
    for author in authors:
        if len(author) != 1:
            bad_authors = False
    if bad_authors:
        return ["".join(authors)]
    
    for author in authors:
        if isinstance(author, str):
            sanitized_authors.append(author)
        else:
            sanitized_authors.append(author['#text'])
    return sanitized_authors


def sanitize_titles(title):
    if isinstance(title, str):
        return title.replace(',', ' ')
    else:
        return (' '.join(title)).replace(',', ' ')


def read_pub(pub_xml):
    pub_type = list(pub_xml['dblp'].keys())[0]

    year = int(pub_xml['dblp'][pub_type]['year'])

    if 'author' in pub_xml['dblp'][pub_type]:
        authors = sanitize_coauthors(pub_xml['dblp'][pub_type]['author'])
    else:
        authors = []

    return {'key': pub_xml['dblp'][pub_type]['@key'],
            'title': sanitize_titles(pub_xml['dblp'][pub_type]['title']),
            'year': year,
            'authors': authors}


#http://dblp.uni-trier.de/rec/rdf/conf/isca/KannanGGS17.rdf
def request_publication(key):
    xmldict = request_dblp('rec/bibtex/%s.xml' % key)
    rdfdict = request_dblp('rec/rdf/%s.rdf' % key)
    return xmldict, rdfdict

def request_publications(author_key):
    pubs = []
    try :
        publication_keys = request_publication_keys(author_key)

        with Pool(NP) as pool:
            pubs = [read_pub(pub.get()[0]) for pub in tqdm([pool.apply_async(request_publication, args=(key,)) for key in publication_keys]) if pub ]

    except Exception as err:
        print("Something bad happend:", str(err))

    # for key in tqdm(publication_keys):
    #     pub, _ = request_publication(key)
    #     if pub:
    #         pubs.append(read_pub(pub))

    return pubs


def is_blacklisted(blacklist, key):
    for b in blacklist:
        if b in key:
            return True

    return False


def filter_publications(publications, year):
    blacklist = []

    return [pub for pub in publications
            if (not is_blacklisted(blacklist, pub['key']) and
                pub['year'] >= year)]


def get_author_keys(author_list):
    authors = read_csv(author_list, ["first_name", "last_name"])

    for author in tqdm(authors):
        keys = request_author_key(author["first_name"] + "+" +
                                  author["last_name"])
        author["keys"] = keys

    return authors


def build_author_key_csv(author_key_list, authors):
    csv = []
    for author in authors:
        row = [author['id'], author['first_name'], author['last_name']]
        for key in author['keys']:
            csv += [row + [key, 'x', make_author_link(key)]]

    write_csv(author_key_list, ['id', 'first_name', 'last_name', 'key',
                                'valid', 'key_link'], csv)


def build_paper_csv(pub_list, authors, whitelist):
    schema = ['id', 'first_name', 'last_name', 'keys',
              'valid', 'pub_key', 'pub_title', 'put_year', 'pub_authors']
    csv = []
    for k, author in authors.items():
        row = [k, author['first_name'], author['last_name'],
               ";".join(author['keys']), 'x']
        for pub in author['pubs']:
            csv += [row + [pub['key'], pub['title'], pub['year'],
                           ';'.join(pub['authors'])]]
    write_csv(pub_list, schema, csv)


def get_paper_list(author_keys, year):
    author_keys = read_csv(author_keys, ['first_name', 'last_name',
                                         'key', 'valid', 'key_link'])
    authors = {}
    # Adding authors with multiple keys
    for entry in author_keys:
        idx = entry['id']
        if idx not in authors and entry['valid']:
            authors[idx] = {}
            copy_dic(entry, authors[idx], ['first_name', 'last_name'])
            authors[idx]['keys'] = [entry['key']]
        elif entry['valid']:
            authors[idx]['keys'].append(entry['key'])

    print("looping over authors")
    for idx, v in authors.items():
        print(v)
        print("processing %d" % idx)
        v['pubs'] = []
        for k in v['keys']:
            v['pubs'].extend(filter_publications(request_publications(k),
                                                 year))

    return authors


def get_co_authors(paper_csv):
    papers = read_csv(paper_csv, ['first_name', 'last_name',
                                  'keys', 'valid', 'pub_key', 'pub_title',
                                  'put_year', 'pub_authors'])
    papers_dic = {}
    for p in papers:
        a_id = int(p['id'])
        if a_id not in papers_dic:
            papers_dic[a_id] = {}
            papers_dic[a_id]['first_name'] = p['first_name']
            papers_dic[a_id]['last_name'] = p['last_name']
            papers_dic[a_id]['keys'] = set([p['keys']])
            papers_dic[a_id]['pubs'] = []
            papers_dic[a_id]['co-authors'] = {}

        a_dic = papers_dic[a_id]

        if p['valid']:
            pub = (p['pub_key'], p['pub_title'])
            a_dic['pubs'].append(pub)
            for co_a in p['pub_authors'].split(";"):
                if co_a not in a_dic['co-authors']:
                    a_dic['co-authors'][co_a] = [pub]
                else:
                    a_dic['co-authors'][co_a].append(pub)

    return papers_dic


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["author-keys", "paper-list",
                                         "list-co-authors", "get-conflicts"])
    parser.add_argument("--author-list", help="List with author names")
    parser.add_argument("--author-keys",
                        help="List with author keys to be searched")
    parser.add_argument("--paper-list",
                        help="Author paper list")
    parser.add_argument("--co-author-list", help="Co author list")
    parser.add_argument("--co-author-year", type=int,
                        default=2012,
                        help="Last acceptable year for"
                        "collaboration without conflict")

    # These optaions are not implemented yet
    parser.add_argument("--pc-conflicts",
                        help="File with conflicts listed by pc member")
    parser.add_argument("--pc-conflicts-new-csv",
                        help="New conflicts found in DBLP. CSV to be"
                        " fed to hotcrp")
    parser.add_argument("--pc-conflicts-new-report",
                        help="New conflicts found in DBLP. File with report to"
                        " be sent to PC members")
    parser.add_argument("--hot-crp-papers",
                        help="JSON with hotcrp papers, will be used to"
                        " generate the conflict list")
    parser.add_argument("-n",
                        default=2, type=int,
                        help="# of parallel threads")

    args = parser.parse_args()

    global NP; NP = args.n

    def check_arg(arg, msg):
        if not arg:
            parser.print_help()
            raise ValueError(msg)

    if args.mode == 'author-keys':
        check_arg(args.author_list, "No author list passed")

        authors = get_author_keys(args.author_list)
        build_author_key_csv(args.author_keys, authors)

    elif args.mode == 'paper-list':
        check_arg(args.author_keys, "No author keys passed")
        check_arg(args.paper_list, "No paper list passed")

        authors = get_paper_list(args.author_keys,
                                 args.co_author_year)
        # build_paper_csv(args.paper_list, authors, args.drop_conf_whitelist)
        build_paper_csv(args.paper_list, authors, True)

    elif args.mode == 'list-co-authors':
        check_arg(args.paper_list, "No paper list passed")

        papers_dic = get_co_authors(args.paper_list)
        for k, v in papers_dic.items():
            print(k)
            print(v)

if __name__ == '__main__':
    main()
    save_cache()
