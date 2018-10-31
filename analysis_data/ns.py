#encoding:utf-8

from collections import Counter


def analyze_ns():
    ns_counter = Counter()
    single_ns_counter = Counter()
    unique_ns = []
    fp = open('NS.txt', 'r')
    domain_ns = fp.readlines()
    for d_n in domain_ns:
        if d_n:
            domain, ns = d_n.split('\t')[0],d_n.split('\t')[1]
            ns = ns.strip().lower()
            ns_list = sorted(ns.split(';'))  # 排序
            for i in ns_list:
                single_ns_counter[i] += 1
            unique_ns.extend(ns_list)
            ns = ';'.join(ns_list)
            ns_counter[ns] += 1

    unique_ns = list(set(unique_ns))
    print len(ns_counter)
    print len(unique_ns)

    for i, j in ns_counter.most_common(10):
        print i, j

    # for i,j in single_ns_counter.most_common(10):
    #     print i,j


    fp.close()


analyze_ns()
