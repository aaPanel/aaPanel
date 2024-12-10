import{_ as a}from"./index96.js?v=1732601582185";import{_ as e}from"./index.vue_vue_type_script_setup_true_lang.js?v=1732601582185";import{d as s,W as t,V as o,r as l,j as r,O as d,P as p,M as n,Y as u,Q as _,R as b,X as i,ao as c,Z as m,ak as v}from"./vue.js?v=1732601582185";import{aa as x,cz as h,bC as w,cA as f,cB as g}from"./page_layout.js?v=1732601582185";import{v as D}from"./index230.js?v=1732601582185";import{ad as $,bG as y,bl as j}from"./naive.js?v=1732601582185";const k={class:"p-20px"},q={class:"w-260px"},U={class:"w-260px"},E={class:"w-260px"},C={class:"w-260px"},R={class:"w-260px"},M={key:0},z=s({__name:"form",props:{data:{}},setup(s,{expose:z}){const{t:A}=t(),B=s,{row:G,isEdit:N}=B.data,O=x(),{type:P}=o(O),Q=l(null),V=r({db_host:"",db_port:null,db_user:"root",db_password:"",db_ps:""}),W={db_host:{trigger:["blur","change"],validator:(a,e)=>""===e?new Error(A("Database.tools.index_53")):!(!h(e)&&!w(e))||new Error(A("Database.tools.index_54"))},db_port:D(),db_user:{required:!0,message:A("Database.tools.index_55"),trigger:["blur","change"]},db_password:{required:!0,message:A("Database.tools.index_56"),trigger:["blur","change"]}},X=a=>{V.db_ps=a},Y=new Map([["mysql",{port:3306,username:"root"}],["sqlserver",{port:1433,username:"sa"}],["redis",{port:6379,username:"root"}],["mongodb",{port:27017,username:"root"}],["pgsql",{port:5432,username:"postgres"}]]);return(()=>{if(N&&G)V.db_host="".concat(G.db_host),V.db_port=G.db_port,V.db_user="".concat(G.db_user),V.db_password="".concat(G.db_password),V.db_ps="".concat(G.ps);else{const a=Y.get(P.value);a&&(V.db_port=a.port,V.db_user=a.username)}})(),z({onConfirm:async({hide:a})=>{var e;await(null==(e=Q.value)?void 0:e.validate());const s=(()=>{const{db_port:a}=V;if(null===a)throw new Error(A("Database.tools.index_57"));return{...v(V),db_port:a,type:P.value}})();N&&G&&await f(P.value,{id:G.id,...s}),N||await g(P.value,s),O.getRemote(),a()}}),(s,t)=>{const o=$,l=y,r=j,v=e,x=a;return d(),p("div",k,[n(v,{ref_key:"formRef",ref:Q,model:b(V),rules:W},{default:u((()=>[n(l,{label:s.$t("Database.tools.index_42"),path:"db_host"},{default:u((()=>[_("div",q,[n(o,{value:b(V).db_host,"onUpdate:value":[t[0]||(t[0]=a=>b(V).db_host=a),X],placeholder:s.$t("Database.tools.index_43"),"input-props":{name:"host"}},null,8,["value","placeholder"])])])),_:1},8,["label"]),n(l,{label:s.$t("Docker.Container.create.index_7"),path:"db_port"},{default:u((()=>[_("div",U,[n(r,{value:b(V).db_port,"onUpdate:value":t[1]||(t[1]=a=>b(V).db_port=a),min:1,max:65535,"show-button":!1,"input-props":{name:"port"},placeholder:s.$t("Database.tools.index_44")},null,8,["value","placeholder"])])])),_:1},8,["label"]),"redis"!==b(P)?(d(),i(l,{key:0,label:s.$t("Database.index_13"),path:"db_user"},{default:u((()=>[_("div",E,[n(o,{value:b(V).db_user,"onUpdate:value":t[2]||(t[2]=a=>b(V).db_user=a),placeholder:s.$t("Database.tools.index_45"),"input-props":{name:"username"}},null,8,["value","placeholder"])])])),_:1},8,["label"])):c("",!0),n(l,{label:s.$t("Database.index_14"),path:"db_password"},{default:u((()=>[_("div",C,[n(o,{value:b(V).db_password,"onUpdate:value":t[3]||(t[3]=a=>b(V).db_password=a),placeholder:s.$t("Database.tools.index_46"),"input-props":{name:"password"}},null,8,["value","placeholder"])])])),_:1},8,["label"]),n(l,{label:"Notes",path:"db_ps","show-feedback":!1},{default:u((()=>[_("div",R,[n(o,{value:b(V).db_ps,"onUpdate:value":t[4]||(t[4]=a=>b(V).db_ps=a),placeholder:s.$t("Database.tools.index_48"),"input-props":{name:"ps"}},null,8,["value","placeholder"])])])),_:1})])),_:1},8,["model"]),n(x,{class:"mt-24px"},{default:u((()=>["mysql"===b(P)?(d(),p("li",M,m(s.$t("Database.tools.index_49")),1)):c("",!0),_("li",null,m(s.$t("Database.tools.index_50")),1),_("li",null,m(s.$t("Database.tools.index_51")),1),_("li",null,m(s.$t("Database.tools.index_52")),1)])),_:1})])}}});export{z as _};