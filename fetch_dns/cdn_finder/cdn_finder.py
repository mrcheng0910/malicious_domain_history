# encoding:utf-8

from cdn_list import CDN_PROVIDER
# from reverse_cname import domain2cname
import DNS


def resolve_domain_record(domain):
    """
    获取解析到的域名ip和cname列表
    """
    cnames = []
    req_obj = DNS.Request()
    try:
        answer_obj = req_obj.req(name=domain, qtype=DNS.Type.A, server="223.5.5.5")
        for i in answer_obj.answers:
            if i['typename'] == 'CNAME':
                cnames.append(i['data'])
    except DNS.Base.DNSError:
        cnames = []

    return cnames


def cdn_finder(host):
    for cdn in CDN_PROVIDER:
        if cdn[0] in host:
            return cdn[1]
    return None


domains = [
'879.com',
'903903cc.com',
'0805.com',
'188.com',
'32333.com',
'3366.com',
'66555.com',
'668cp.bz',
'668cp.cc',
'668cp.co',
'aliyun.com',
'cctv.com',
'cnmo.com',
'ctrip.com.hk',
'd08888.com',
'd11188.com',
'd11199.com',
'd44466.com',
'd55566.com',
'd66.com',
'd6669.com',
'd88866.com',
'd99988.com',
'dl8.com',
'guibin07.com',
'hg33.com',
'hg7177.com',
'jy4f.com',
'kwm.com',
'm0003.com',
'm0004.com',
'maicai.cn',
'qianggongzhang.com',
'quduo8.com',
'vns88666.com',
'vv511.com',
'vv577.com',
'yingle99.net',
'youquba.net',
'003807.net',
'11605.com',
'77100.com',
'd1119.com',
'd33366.com',
'd77788.com',
'hg3308.com',
'hg5321.com',
'hg767.com',
'mgm0015.com',
'mgm288.cc',
'xinhui.gov.cn',
'zhongguotongcuhui.org.cn',
'zt9903.com',
'34797.com',
'gwytb.gov.cn',
'kankannews.com',
'0504345.com',
'009bai.com',
'04755.com',
'0504456.com',
's36366.com',
'hg6699dd.com',
'pj9567.com',
'903903hh.com',
'9812z.com',
'100336.net',
'009bai.net',
'1683168.com',
's1386.com',
'0612b.com',
'9812b.com',
'swj1.com',
'0504234.com',
'99135.com',
'www-15222.com',
'99135m.com',
'903903bb.com',
'10209.com',
'hg6678.com',
'hg33833.net',
'903903gg.com',
'90022.com',
'feilipu1.com',
'01128.am',
'9812d.com',
'99136m.com',
'100335.com',
'hg5053.com',
'sun0063.com',
'hg878.co',
'44321.com',
'08977p.com',
'90011.com',
'sportdafa.com',
'3648850.com',
'zt822.com',
'haobo5566.com',
'rr7720.com',
'hg6205.com',
'hg6207.com',
'903903ff.com',
'hg933.com',
'98428.com',
'001sg.com',
'd33388.com',
'527714.com',
'm0002.com',
'006006.co',
'4yh76.com',
'd66688.com',
'ff0009.com',
'hg905.com',
'9812c.com',
'hg6206.com',
'hg33.nl',
'537714.com',
'03355.com',
'pj43.com',
'hg1086.com',
'v22221.com',
'9812a.com',
'903903ee.com',
'hg33.im',
'517714.com',
'050.com',
'9320123.com',
'044js.com',
'05599.com',
'0504123.com',
'aamm22.com',
'02282.am',
'100338.net',
'5364o.com',
'0504678.com',
'9340123.com',
'9812e.com',
'hg6203.com',
'98895.com',
'012.com',
'01001.com',
'pj42.com',
'pj1567.com',
'hg88866.com',
'967.cc'
]

a = 'd'
domains = ['taobao.com']
def main():

    for i in domains[:10]:
        print 'domain: ', i
        cnames = resolve_domain_record("www."+i)

        for host in cnames:
            print cdn_finder(host)

if __name__ == '__main__':
    main()
