import tldextract



def manage_phishtank():

    fp = open('malware_domains.txt','r')
    fw = open('malware_domains_data.txt','a')
    for i in fp.readlines():
        try:
            domain_tld = tldextract.extract(i.strip())
            if not domain_tld.suffix:
                continue
            check_domain = domain_tld.domain+'.'+domain_tld.suffix
            print check_domain
            fw.write(check_domain+'\n')

        except:
            continue


    fp.close()
    fw.close()

manage_phishtank()