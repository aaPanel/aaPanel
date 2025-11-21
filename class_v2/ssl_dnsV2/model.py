# coding: utf-8
# -------------------------------------------------------------------
# aaPanel
# -------------------------------------------------------------------
# Copyright (c) 2014-2099 aaPanel(www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: aapanel
# -------------------------------------------------------------------

# ------------------------------
# dns app
# ------------------------------
from public.aaModel import *


class DnsResolve(aaModel):
    id = IntField(primary_key=True)
    domain = StrField(default="", ps="domain")
    ns_resolve = IntField(default=0, ps="NS")
    a_resolve = IntField(default=0, ps="A")
    tips = StrField(default="", ps="tips")

    create_time = DateTimeStrField(auto_now_add=True, ps="创建时间")
    update_time = DateTimeStrField(auto_now=True, ps="更新时间")

    @classmethod
    def update_or_create(cls, domain: str, **kwargs) -> "DnsResolve":
        obj = cls.objects.filter(domain=domain).first()
        if obj:
            for k, v in kwargs.items():
                setattr(obj, k, v)
            obj.save()
            return obj
        else:
            res = cls(domain=domain, **kwargs).save()
            return res

    class _Meta:
        table_name = "dns_domain_resolve"
        index = [
            "domain"
        ]
