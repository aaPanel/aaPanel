import{_ as a}from"./index.js?v=1732601582185";import{_ as e}from"./index.vue_vue_type_script_setup_true_lang.js?v=1732601582185";import{I as t,m as s}from"./page_layout.js?v=1732601582185";import{h as l,d as i,f as n,a as o}from"./public.js?v=1732601582185";import{r as d,g as r,t as m,u}from"./planned.js?v=1732601582185";import{ad as c,aa as p,bh as _,bR as f,bG as v}from"./naive.js?v=1732601582185";import{d as x,W as h,r as w,j as P,O as b,P as j,M as y,Y as g,Q as H,R as S,ac as k,c as C,Z as R,ak as U}from"./vue.js?v=1732601582185";import"./common.js?v=1732601582185";import"./__commonjsHelpers__.js?v=1732601582185";const $={class:"p-20px"},B={class:"flex-1"},D={class:"mt-12px"},O={class:"px-20px pt-24px pb-8px"},q={class:"w-150px"},E=x({__name:"set",props:{data:{}},setup(x){const{t:E}=h(),G=x,{setOptions:I}=G.data,M=w(""),Q=async()=>{const a=M.value.trim();""!==a?(await m({name:a}),M.value="",await K(),null==I||I(F.data)):s.error(E("Site.PHP.index_46"))},W=l(),Y=w(null),Z=P({id:-1,name:""}),z={name:{required:!0,message:E("Site.PHP.index_46"),trigger:["blur","change"]}},A=async({hide:a})=>{var e;await(null==(e=Y.value)?void 0:e.validate()),await u(U(Z)),await K(),null==I||I(F.data),a()},{table:F,columns:J}=i([{key:"name",title:E("Docker.Compose.form.index_3")},n({width:80,options:a=>[{label:E("Public.Btn.Edit"),disabled:0===a.id,onClick:()=>{(a=>{Z.id=a.id,Z.name=a.name,W.title="".concat(E("Site.PHP.index_48")," [").concat(a.name,"]"),W.show=!0})(a)}},{label:E("Public.Btn.Del"),disabled:0===a.id,onClick:()=>{o({title:"".concat(E("Site.PHP.index_49")," [").concat(a.name,"]"),content:E("Site.PHP.index_50"),onConfirm:async({hide:e})=>{await d({id:a.id}),await K(),null==I||I(F.data,a.id),e()}})}}]})]),K=async()=>{const{message:a}=await r();F.data=t(a)?a:[]};return K(),(t,s)=>{const l=c,i=p,n=_,o=f,d=v,r=e,m=a;return b(),j("div",$,[y(n,null,{default:g((()=>[H("div",B,[y(l,{value:S(M),"onUpdate:value":s[0]||(s[0]=a=>k(M)?M.value=a:null),placeholder:t.$t("Site.PHP.index_46")},null,8,["value","placeholder"])]),H("div",null,[y(i,{type:"primary",onClick:Q},{default:g((()=>[C(R(t.$t("Site.Cert.index_62")),1)])),_:1})])])),_:1}),H("div",D,[y(o,{"max-height":300,data:S(F).data,columns:S(J)},null,8,["data","columns"])]),y(m,{show:S(W).show,"onUpdate:show":s[2]||(s[2]=a=>S(W).show=a),title:S(W).title,width:350,footer:!0,onConfirm:A},{default:g((()=>[H("div",O,[y(r,{ref_key:"formRef",ref:Y,model:S(Z),rules:z},{default:g((()=>[y(d,{label:t.$t("Site.PHP.index_47"),path:"name"},{default:g((()=>[H("div",q,[y(l,{value:S(Z).name,"onUpdate:value":s[1]||(s[1]=a=>S(Z).name=a),placeholder:""},null,8,["value"])])])),_:1},8,["label"])])),_:1},8,["model"])])])),_:1},8,["show","title"])])}}});export{E as default};