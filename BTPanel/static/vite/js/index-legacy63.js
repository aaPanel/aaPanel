System.register(["./index-legacy64.js?v=1721298337096","./index-legacy.js?v=1721298337096","./pinia-legacy.js?v=1721298337096","./vue-legacy.js?v=1721298337096","./useTableColumns-legacy.js?v=1721298337096","./Select-legacy.js?v=1721298337096"],(function(e,t){"use strict";var a,i,n,o,l,s,d,c,r,u,m,p,v,f,g,h,y,x,w,j,b,_,H,k,C,D,B;return{setters:[e=>{a=e._},e=>{i=e.u,n=e.H,o=e.I,l=e.e,s=e.J,d=e.v},e=>{c=e.s},e=>{r=e.l,u=e.S,m=e.U,p=e.V,v=e.W,f=e.Z,g=e.P,h=e.q,y=e.F,x=e.af,w=e.D,j=e._,b=e.ah,_=e.k,H=e.ai,k=e.a1},e=>{C=e.s,D=e.g},e=>{B=e._}],execute:function(){e({a:function(e){s({title:`Database Backup Details [${e.name}]`,width:700,minHeight:196,data:{row:e},component:k((()=>d((()=>t.import("./index-legacy77.js?v=1721298337096")),void 0)))})},b:function(e){s({title:`Import to database from file [${e.name}]`,width:680,minHeight:234,data:{row:e},component:k((()=>d((()=>t.import("./index-legacy78.js?v=1721298337096")),void 0)))})},c:function(e){s({title:"Delete database",width:760,minHeight:226,footer:!0,confirmType:"error",confirmText:"Next",data:{ids:e.map((e=>e.id))},component:k((()=>d((()=>t.import("./index-legacy80.js?v=1721298337096")),void 0)))})},d:function(){s({title:"Select database location",width:460,minHeight:85,footer:!0,component:k((()=>d((()=>t.import("./index-legacy76.js?v=1721298337096")),void 0)))})},f:function(){s({title:"Change database password",width:480,minHeight:84,footer:!0,component:k((()=>d((()=>t.import("./index-legacy75.js?v=1721298337096")),void 0)))})},g:function(){s({title:"Remote DB list",width:860,minHeight:264,component:k((()=>d((()=>t.import("./index-legacy74.js?v=1721298337096")),void 0)))})},u:function(e){s({title:`Change the database password [${e.name}]`,width:480,minHeight:140,footer:!0,data:{row:e},component:k((()=>d((()=>t.import("./index-legacy79.js?v=1721298337096")),void 0)))})}});const S=j("span",{class:"mr-4px"},"The remote server is not configured, ",-1),$=j("span",{class:"mx-4px"},"|",-1),T=(e("e",r({__name:"index",setup(e){const t=i(),{type:s,install:d}=c(t),r=()=>{"pgsql"===s.value?n():o(s.value)};return(e,t)=>{const i=l,n=a;return u(),m(n,{install:v(d)},{desc:p((()=>[S,"sqlserver"!==v(s)?(u(),f(y,{key:0},[g(i,{onClick:r},{default:p((()=>[h("Click install")])),_:1}),$],64)):x("",!0),g(i,{onClick:v(q)},{default:p((()=>[h("Add Remote DB")])),_:1},8,["onClick"])])),default:p((()=>[w(e.$slots,"default")])),_:3},8,["install"])}}})),{class:"w-120px"});function q(){s({title:"Add Remote DB",width:460,minHeight:388,footer:!0,data:{row:void 0,isEdit:!1},component:k((()=>d((()=>t.import("./form-legacy.js?v=1721298337096")),void 0)))})}e("_",r({__name:"index",props:b({storeKey:{default:""},value:{},all:{type:Boolean,default:!0}},{value:{},valueModifiers:{}}),emits:b(["change"],["update:value"]),setup(e,{emit:t}){const a=e,n=t,o=_((()=>{const{storeKey:e}=a;return e?`${e}-select`:""})),l=H(e,"value"),s=i(),{remoteList:d}=c(s),r=_((()=>{const e=d.value.map((e=>({label:e.ps||e.db_host,value:e.id})));return a.all&&e.unshift({label:"All",value:-1}),e})),m=e=>{o.value&&C(o.value,String(e)),n("change",e)};return(()=>{if(o.value){const e=D(o.value);e&&(l.value=Number(e))}})(),(e,t)=>{const a=B;return u(),f("div",T,[g(a,{value:l.value,"onUpdate:value":[t[0]||(t[0]=e=>l.value=e),m],options:v(r)},null,8,["value","options"])])}}}))}}}));