# encoding:utf-8

from collections import Counter


def privacy():


    domain_count = 0
    registrar,reg_name = Counter(),Counter()
    fp = open('privacy.txt','r')
    domains = fp.readlines()
    print len(domains)
    for d in domains:
        d = d.strip()
        try:
            registrar[d.split('\t')[1]] += 1
            reg_name[d.split('\t')[2]] += 1
        except:
            pass

    for i,j in registrar.most_common(10):
        print i, '\t', j
    print '-------------------------------------'
    for i,j in reg_name.most_common():
        print i, '\t', j
    fp.close()


privacy()