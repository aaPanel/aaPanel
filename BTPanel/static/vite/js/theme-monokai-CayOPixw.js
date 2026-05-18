import{a as _}from"./ace-BbQKG2qL.js?v=1778752098997";import{b8 as A}from"./index-DV9DrNIN.js?v=1778752098997";import{k as h,K as d,au as u,m as g}from"./vue-core-27PG2C1f.js?v=1778752098997";const s=["blur","input","change","changeSelectionStyle","changeSession","copy","focus","paste"],v=h({name:"VAceEditor",props:{value:{type:String,required:!0},lang:{type:String,default:"text"},theme:{type:String,default:"chrome"},options:Object,placeholder:String,readonly:Boolean,wrap:Boolean,printMargin:{type:[Boolean,Number],default:!0},minLines:Number,maxLines:Number},emits:["update:value","init",...s],render(){return g("div")},mounted(){const e=this._editor=d(_.edit(this.$el,{placeholder:this.placeholder,readOnly:this.readonly,value:this.value,mode:"ace/mode/"+this.lang,theme:"ace/theme/"+this.theme,wrap:this.wrap,printMargin:this.printMargin,useWorker:!1,minLines:this.minLines,maxLines:this.maxLines,...this.options}));this._contentBackup=this.value,this._isSettingContent=!1,e.on("change",()=>{if(this._isSettingContent)return;const o=e.getValue();this._contentBackup=o,this.$emit("update:value",o)}),s.forEach(o=>{const n="on"+u(o);typeof this.$.vnode.props[n]=="function"&&e.on(o,this.$emit.bind(this,o))}),this._ro=new A(()=>e.resize()),this._ro.observe(this.$el),this.$emit("init",e)},beforeUnmount(){var e,o;(e=this._ro)===null||e===void 0||e.disconnect(),(o=this._editor)===null||o===void 0||o.destroy()},methods:{focus(){this._editor.focus()},blur(){this._editor.blur()},selectAll(){this._editor.selectAll()},getAceInstance(){return this._editor}},watch:{value(e){if(this._contentBackup!==e){try{this._isSettingContent=!0,this._editor.setValue(e,1)}finally{this._isSettingContent=!1}this._contentBackup=e}},theme(e){this._editor.setTheme("ace/theme/"+e)},options(e){this._editor.setOptions(e)},readonly(e){this._editor.setReadOnly(e)},placeholder(e){this._editor.setOption("placeholder",e)},wrap(e){this._editor.setWrapBehavioursEnabled(e)},printMargin(e){this._editor.setOption("printMargin",e)},lang(e){this._editor.setOption("mode","ace/mode/"+e)},minLines(e){this._editor.setOption("minLines",e)},maxLines(e){this._editor.setOption("maxLines",e)}}});var t={exports:{}},m;function p(){return m||(m=1,(function(e,o){ace.define("ace/theme/chrome-css",["require","exports","module"],function(n,a,c){c.exports=`.ace-chrome .ace_gutter {
  background: #ebebeb;
  color: #333;
  overflow : hidden;
}

.ace-chrome .ace_print-margin {
  width: 1px;
  background: #e8e8e8;
}

.ace-chrome {
  background-color: #FFFFFF;
  color: black;
}

.ace-chrome .ace_cursor {
  color: black;
}

.ace-chrome .ace_invisible {
  color: rgb(191, 191, 191);
}

.ace-chrome .ace_constant.ace_buildin {
  color: rgb(88, 72, 246);
}

.ace-chrome .ace_constant.ace_language {
  color: rgb(88, 92, 246);
}

.ace-chrome .ace_constant.ace_library {
  color: rgb(6, 150, 14);
}

.ace-chrome .ace_invalid {
  background-color: rgb(153, 0, 0);
  color: white;
}

.ace-chrome .ace_fold {
}

.ace-chrome .ace_support.ace_function {
  color: rgb(60, 76, 114);
}

.ace-chrome .ace_support.ace_constant {
  color: rgb(6, 150, 14);
}

.ace-chrome .ace_support.ace_type,
.ace-chrome .ace_support.ace_class
.ace-chrome .ace_support.ace_other {
  color: rgb(109, 121, 222);
}

.ace-chrome .ace_variable.ace_parameter {
  font-style:italic;
  color:#FD971F;
}
.ace-chrome .ace_keyword.ace_operator {
  color: rgb(104, 118, 135);
}

.ace-chrome .ace_comment {
  color: #236e24;
}

.ace-chrome .ace_comment.ace_doc {
  color: #236e24;
}

.ace-chrome .ace_comment.ace_doc.ace_tag {
  color: #236e24;
}

.ace-chrome .ace_constant.ace_numeric {
  color: rgb(0, 0, 205);
}

.ace-chrome .ace_variable {
  color: rgb(49, 132, 149);
}

.ace-chrome .ace_xml-pe {
  color: rgb(104, 104, 91);
}

.ace-chrome .ace_entity.ace_name.ace_function {
  color: #0000A2;
}


.ace-chrome .ace_heading {
  color: rgb(12, 7, 255);
}

.ace-chrome .ace_list {
  color:rgb(185, 6, 144);
}

.ace-chrome .ace_marker-layer .ace_selection {
  background: rgb(181, 213, 255);
}

.ace-chrome .ace_marker-layer .ace_step {
  background: rgb(252, 255, 0);
}

.ace-chrome .ace_marker-layer .ace_stack {
  background: rgb(164, 229, 101);
}

.ace-chrome .ace_marker-layer .ace_bracket {
  margin: -1px 0 0 -1px;
  border: 1px solid rgb(192, 192, 192);
}

.ace-chrome .ace_marker-layer .ace_active-line {
  background: rgba(0, 0, 0, 0.07);
}

.ace-chrome .ace_gutter-active-line {
    background-color : #dcdcdc;
}

.ace-chrome .ace_marker-layer .ace_selected-word {
  background: rgb(250, 250, 255);
  border: 1px solid rgb(200, 200, 250);
}

.ace-chrome .ace_storage,
.ace-chrome .ace_keyword,
.ace-chrome .ace_meta.ace_tag {
  color: rgb(147, 15, 128);
}

.ace-chrome .ace_string.ace_regex {
  color: rgb(255, 0, 0)
}

.ace-chrome .ace_string {
  color: #1A1AA6;
}

.ace-chrome .ace_entity.ace_other.ace_attribute-name {
  color: #994409;
}

.ace-chrome .ace_indent-guide {
  background: url("data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAACCAYAAACZgbYnAAAAE0lEQVQImWP4////f4bLly//BwAmVgd1/w11/gAAAABJRU5ErkJggg==") right repeat-y;
}
  
.ace-chrome .ace_indent-guide-active {
  background: url("data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAACCAYAAACZgbYnAAAACXBIWXMAAAsTAAALEwEAmpwYAAAAIGNIUk0AAHolAACAgwAA+f8AAIDpAAB1MAAA6mAAADqYAAAXb5JfxUYAAAAZSURBVHjaYvj///9/hivKyv8BAAAA//8DACLqBhbvk+/eAAAAAElFTkSuQmCC") right repeat-y;
}
`}),ace.define("ace/theme/chrome",["require","exports","module","ace/theme/chrome-css","ace/lib/dom"],function(n,a,c){a.isDark=!1,a.cssClass="ace-chrome",a.cssText=n("./chrome-css");var r=n("../lib/dom");r.importCssString(a.cssText,a.cssClass,!1)}),(function(){ace.require(["ace/theme/chrome"],function(n){e&&(e.exports=n)})})()})(t)),t.exports}p();var i={exports:{}},l;function k(){return l||(l=1,(function(e,o){ace.define("ace/theme/monokai-css",["require","exports","module"],function(n,a,c){c.exports=`.ace-monokai .ace_gutter {
  background: #2F3129;
  color: #8F908A
}

.ace-monokai .ace_print-margin {
  width: 1px;
  background: #555651
}

.ace-monokai {
  background-color: #272822;
  color: #F8F8F2
}

.ace-monokai .ace_cursor {
  color: #F8F8F0
}

.ace-monokai .ace_marker-layer .ace_selection {
  background: #49483E
}

.ace-monokai.ace_multiselect .ace_selection.ace_start {
  box-shadow: 0 0 3px 0px #272822;
}

.ace-monokai .ace_marker-layer .ace_step {
  background: rgb(102, 82, 0)
}

.ace-monokai .ace_marker-layer .ace_bracket {
  margin: -1px 0 0 -1px;
  border: 1px solid #49483E
}

.ace-monokai .ace_marker-layer .ace_active-line {
  background: #202020
}

.ace-monokai .ace_gutter-active-line {
  background-color: #272727
}

.ace-monokai .ace_marker-layer .ace_selected-word {
  border: 1px solid #49483E
}

.ace-monokai .ace_invisible {
  color: #52524d
}

.ace-monokai .ace_entity.ace_name.ace_tag,
.ace-monokai .ace_keyword,
.ace-monokai .ace_meta.ace_tag,
.ace-monokai .ace_storage {
  color: #F92672
}

.ace-monokai .ace_punctuation,
.ace-monokai .ace_punctuation.ace_tag {
  color: #fff
}

.ace-monokai .ace_constant.ace_character,
.ace-monokai .ace_constant.ace_language,
.ace-monokai .ace_constant.ace_numeric,
.ace-monokai .ace_constant.ace_other {
  color: #AE81FF
}

.ace-monokai .ace_invalid {
  color: #F8F8F0;
  background-color: #F92672
}

.ace-monokai .ace_invalid.ace_deprecated {
  color: #F8F8F0;
  background-color: #AE81FF
}

.ace-monokai .ace_support.ace_constant,
.ace-monokai .ace_support.ace_function {
  color: #66D9EF
}

.ace-monokai .ace_fold {
  background-color: #A6E22E;
  border-color: #F8F8F2
}

.ace-monokai .ace_storage.ace_type,
.ace-monokai .ace_support.ace_class,
.ace-monokai .ace_support.ace_type {
  font-style: italic;
  color: #66D9EF
}

.ace-monokai .ace_entity.ace_name.ace_function,
.ace-monokai .ace_entity.ace_other,
.ace-monokai .ace_entity.ace_other.ace_attribute-name,
.ace-monokai .ace_variable {
  color: #A6E22E
}

.ace-monokai .ace_variable.ace_parameter {
  font-style: italic;
  color: #FD971F
}

.ace-monokai .ace_string {
  color: #E6DB74
}

.ace-monokai .ace_comment {
  color: #75715E
}

.ace-monokai .ace_indent-guide {
  background: url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAACCAYAAACZgbYnAAAAEklEQVQImWPQ0FD0ZXBzd/wPAAjVAoxeSgNeAAAAAElFTkSuQmCC) right repeat-y
}

.ace-monokai .ace_indent-guide-active {
  background: url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAACCAYAAACZgbYnAAAAEklEQVQIW2PQ1dX9zzBz5sz/ABCcBFFentLlAAAAAElFTkSuQmCC) right repeat-y;
}
`}),ace.define("ace/theme/monokai",["require","exports","module","ace/theme/monokai-css","ace/lib/dom"],function(n,a,c){a.isDark=!0,a.cssClass="ace-monokai",a.cssText=n("./monokai-css");var r=n("../lib/dom");r.importCssString(a.cssText,a.cssClass,!1)}),(function(){ace.require(["ace/theme/monokai"],function(n){e&&(e.exports=n)})})()})(i)),i.exports}k();export{v as V};
