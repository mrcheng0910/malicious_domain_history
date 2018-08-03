# encoding:utf-8

from collections import Counter


def domain_age():


    domain_count = 0
    c = Counter()
    fp = open('domain_age.txt','r')
    domains = fp.readlines()
    print len(domains)
    for d in domains:
        c[int(d.strip())] += 1

    for i in range(0, 7):
        print i
        domain_count += c[i]


    print domain_count

    fp.close()


def update():
    domain_count = 0
    c = Counter()
    fp = open('last_updated.txt', 'r')
    domains = fp.readlines()
    total_domains = len(domains)
    for d in domains:
        c[int(d.strip())] += 1
    print total_domains
    for i in range(37, 3700):
        print i, '\t', c[i]
        domain_count += c[i]

    print float(domain_count)/total_domains

    fp.close()




# domain_age()
update()

