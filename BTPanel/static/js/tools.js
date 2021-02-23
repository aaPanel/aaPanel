var bt_tools = {
    /**
     * @description 表格渲染
     * @param {object} config  配置对象 参考说明
     * @return 当前实例对象
    */
    table:function(config){
        function ReaderTable(config){
            this.config = config;
            this.$load();
        }
        ReaderTable.prototype = {
            style_list:[], // 样式列表
            event_list:{}, // 事件列表,已绑定事件
            checkbox_list:[], // 元素选中列表
            batch_active:{},
            event_rows_model:{},// 事件行内元素模型，行内元素点击都会将数据临时存放
            data:[],
            page:'',
            column:[],
            batch_thread:[],
            random:bt.get_random(5),
            init:false, // 是否初始化渲染
            checked:false, // 是否激活，用来判断是否失去焦点
            /**
             * @description 加载数据
             * @return void
             */
            $load:function(){
                var _that = this,$checked = $('<input type="checkbox" id="checked_'+ _that.random +'" style="font-size:0;position:fixed;left:-9999999px;"/>');
                if(this.config.init) this.config.init(this);
                $(this.config.el).addClass('bt_table').append($checked);
                $checked.focus(function(){ 
                    _that.checked = true;
                    return false;
                }).blur(function(ev){ 
                    _that.checked = false;
                    if(_that.checked_blur) _that.checked_blur(ev);
                });
                if(this.config.minWidth) this.style_list.push({className:this.config.el + ' table',css:('min-width:'+this.config.minWidth)});
                if(this.config.tootls){
                    this.$reader_tootls(this.config.tootls);
                }else{
                    if($(_that.config.el +'.divtable').length === 0) $(_that.config.el).append('<div class="divtable mtb10"></div>');
                }
                this.$reader_content();
                if(_that.config.url !== undefined){
                    this.$refresh_table_list();
                }else if(this.config.data !== undefined){
                    this.$reader_content(this.config.data);
                }else {
                    alert(lan.public.miss_data_or_url);
                }
                if(this.config.methods){ //挂载实例方法
                    $.extend(this,this.config.methods);
                }
            },

            /**
             * @description 刷新表格数据
             * @return void
            */
            $refresh_table_list:function(load){
                var _that = this,loadT;
                if(load) loadT = bt.load(lan.database.get_data);
                this.$http(function(data,page){
                    if(load) loadT.close();
                    _that.$reader_content(data,page);
                });
            },
            
            /**
             * @description 激活焦点
             * @param {Function} callback 回调函数
             * @returns void
             */
            $active_focus:function(callback){
                var _that = this;
                $('#checked_'+ _that.random).focus();
                this.checked_blur = function(ev){
                    setTimeout(function(){
                        if(callback) callback(ev);
                        delete _that.checked_blur;
                    },200);
                }
            },
            /**
             * @description 渲染内容
             * @param {object} data 渲染的数据
             * @param {number} page 数据分页
             * @return void
            */
            $reader_content:function(data,page){
                var _that = this,thead = '',tbody = '',i = 0,column = this.config.column,event_list = {},checkbox = $(_that.config.el + ' .checkbox_' + _that.random);
                data = data || [];
                this.data = data;
                if(checkbox.length){
                    checkbox.removeClass('active selected');
                    _that.checkbox_list = [];
                    _that.$set_batch_view();
                }
                do{
                    var rows = data[i],completion = 0;
                    if(data.length > 0) tbody += '<tr>';
                    for(var j=0;j < column.length;j++){
                        var item = column[j];
                        if($.isEmptyObject(item)){
                            completion ++; 
                            continue;
                        }
                        if(i === 0 && !this.init){
                            if(!this.init) this.style_list.push(this.$dynamic_merge_style(item,j - completion));
                            var sortName = 'sort_'+ this.random +'',checkboxName = 'checkbox_'+ this.random,sortValue = item.sortValue || 'desc';
                            thead += '<th><span '+ (item.sort?'class="not-select '+ sortName + (item.sortValue?' sort-active':'') +' cursor-pointer"':'') +' data-index="'+ j +'" '+ (item.sort?'data-sort="'+ sortValue +'"':'') +'>'+ (item.type =="checkbox"?'<label><i class="cust—checkbox cursor-pointer '+ checkboxName +'" data-checkbox="all"></i><input type="checkbox" class="cust—checkbox-input"></label>':'<span>'+ item.title +'</span>') + (item.sort?'<span class="glyphicon glyphicon-triangle-'+ (sortValue == 'desc'?'bottom':'top') +' ml5"></span>':'') +'</span></th>';
                            if(i === 0){
                                if(!event_list[sortName] && item.sort) event_list[sortName] = {event:this.config.sortEvent,eventType:'click',type:'sort'};
                                if(!event_list[checkboxName]) event_list[checkboxName] = {event:item.checked,eventType:'click',type:'checkbox'};
                            }
                        }
                        if(rows !== undefined){
                            var template = '',className = 'event-'+ item.fid +'-'+ this.random;
                            if(item.template){
                                template = _that.$custom_template_render(item,rows,j);
                            }else{
                                template = this.$reader_column_type(item,rows);
                                event_list = $.extend(event_list,template[1]);
                                template = template[0];
                            }
                            tbody += '<td><span '+ (item.class?'class="'+ item.class +'"':'') +' '+ (item.tips?'title="'+ item.tips +'"':'') +'>'+ template +'</span></td>';
                            if(i === 0){
                                if(!event_list[className] && item.event) event_list[className] = {event:item.event,eventType:'click',type:'rows'};
                            }
                        }
                    }
                    if(data.length > 0) tbody += '</tr>'
                    if(data.length == 0) tbody += '<tr><td colspan="'+ (column.length - completion)  +'" style="text-align:center;">'+ (this.config.default || lan.public.empty) +'</td></tr>';
                    i++;
                } while (i < data.length);
                if(!this.init) this.$style_bind(this.style_list);
                this.$event_bind(event_list);
                if(!this.init){
                    $(this.config.el + ' .divtable').append('<table class="table table-hover"><thead>'+ thead +'</thead><tbody>'+ tbody +'</tbody></table></div></div>');
                }else{
                    $(this.config.el + ' .divtable tbody').html(tbody);
                    if(this.config.page && page){
                        $(this.config.el + ' .page').replaceWith(this.$reader_page(this.config.page,page));
                    }
                }
                this.init = true;
                if(this.config.success) this.config.success(this);
            },
            /**
             * @description 自定模板渲染
             * @param {object} item 当前元素模型
             * @param {object} rows 当前元素数据
             * @param {number} j 当前模板index
             * @return void
            */
            $custom_template_render:function(item,rows,j){
                var className= 'event-'+ item.fid +'-'+ this.random,_template = item.template(rows,j),$template = $(_template);
                if($template.length>0){
                    template = $template.addClass(className)[0].outerHTML;
                }else{
                    if(item.type === 'text'){
                        template = '<span class="'+ className +'">'+ _template +'</span>';
                    }else{
                        template = '<a href="javascript:;" class="btlink '+ className +'">'+ _template +'</a>';
                    }
                }
                return template;
            },
            /**
             * @description 替换table数据
             * @param {string} newValue 内容数据
             * @return void
            */
            $modify_row_data:function(newValue){
                this.event_rows_model.rows = $.extend(this.event_rows_model.rows,newValue);
                var row_model = this.event_rows_model,template = null;
                if(typeof row_model.model.template != 'undefined'){
                    template = $(this.$custom_template_render(row_model.model,row_model.rows,row_model.index));
                }else{
                    template = $(this.$reader_column_type(row_model.model,row_model.rows)[0]);
                }
                row_model.el.replaceWith(template);
                row_model.el = template;
            },
            /**
             * @description 批量执行程序
             * @param {object} config 配置文件
             * @return void
            */
            $batch_success_table:function(config){
                var _that = this;
                bt.open({
                    type:1,
                    title:config.title,
                    area:config.area || ['380px','350px'],
                    shadeClose:false,
                    closeBtn:2,
                    content:config.content || '<div class="batch_title"><span class><span class="batch_icon"></span><span class="batch_text">'+ config.title +' '+lan.public.success+'</span></span></div><div class="fiexd_thead divtable success-layer" style="margin: 15px 30px 15px 30px;overflow: auto;height: 200px;"><table class="table table-hover"><thead><tr><th>'+ config.th +'</th><th style="text-align:right;width:120px;">'+lan.public.result+'</th></tr></thead><tbody>'+ config.html +'</tbody></table></div>',
                    success:function(){
                        _that.$fixed_table_thead('.fiexd_thead');
                    }
                });
            },

            /**
             * @description 删除行内数据
             */
            $delete_table_row:function(index){
                this.data.splice(index,1)
                this.$reader_content(this.data);
            },
            /**
             * @description 固定表头
             * @param {string} el DOM选择器
             * @return void
            */
            $fixed_table_thead:function(el){
                $(el).scroll(function(){
                    var scrollTop = this.scrollTop;
                    this.querySelector('thead').style.transform = 'translateY(' + scrollTop + 'px)';
                });
            },

            /**
             * @description 设置批量操作显示
             * @returns void 无
            */
            $set_batch_view:function(){
                var bt_select_val = $(this.config.el + ' .bt_select_value'),bt_select_btn = $(this.config.el + ' .bt_table_select_group').next();
                if(typeof this.config.batch != "undefined"){ //判断是否存在批量操作
                    var bt_select_btn = $(this.config.el + ' .set_batch_option');
                    if(typeof this.config.batch.config != "undefined"){ // 判断批量操作是多个还是单个
                        if(this.checkbox_list.length > 0){
                            bt_select_btn.removeClass('bt-disabled btn-default').addClass('btn-success').text(lan.public.please_choose+this.batch_active.title +'('+lan.public.selected+ this.checkbox_list.length+')')
                        }else{
                            bt_select_btn.addClass('bt-disabled btn-default').removeClass('btn-success').text(lan.public.please_choose+this.batch_active.title);
                        }
                    }else{
                        var bt_select_val = $(this.config.el + ' .bt_select_value');
                        if(this.checkbox_list.length > 0){
                            bt_select_btn.removeClass('bt-disabled btn-default').addClass('btn-success').prev().removeClass('bt-disabled');
                            bt_select_val.find('em').html('('+lan.public.selected+ this.checkbox_list.length+')');
                        }else{
                            bt_select_btn.addClass('bt-disabled btn-default').removeClass('btn-success').prev().addClass('bt-disabled');
                            bt_select_val.children().eq(0).html(lan.public.please_choose+'<em></em>');
                            bt_select_val.next().find('li').removeClass('active');
                            this.batch_active = {};
                        }
                    }
                }
                return false;
                if(bt_select_val.length > 0){
                    if(this.checkbox_list.length > 0){
                        bt_select_val.find('em').html('('+lan.public.selected+ this.checkbox_list.length+')');
                        bt_select_val.parent().removeClass('bt_disabled');
                        bt_select_btn.removeClass('bt-disabled');
                    }else{
                        bt_select_val.parent().addClass('bt_disabled');
                        bt_select_val.find('.bt_select_tips').html(lan.public.please_choose+'<em></em>');
                        bt_select_btn.addClass('bt-disabled');
                        bt_select_btn.find('.item').removeClass('active');
                        this.batch_active = {};
                    }
                }else{//只有批量按钮的模式
                    var bt_select_batch_btn = $(this.config.el + ' .set_batch_option'),all = $(this.config.el + ' [data-checkbox="all"]');
                    for(var i=0;i<this.config.tootls.length;i++){
                        if(this.config.tootls[i].selectList) bt_select_batch_btn.text(this.config.tootls[i].selectList[0].batch_btn_name);
                    }
                    if(all.hasClass('selected') || all.hasClass('active')){
                        bt_select_batch_btn.removeClass('bt-disabled');
                        var _text = bt_select_batch_btn.text()+' ('+$(this.config.el + ' tbody .cust—checkbox.active').length+lan.site.have_been_selected+')';
                        bt_select_batch_btn.text(_text);
                    }else{
                        bt_select_batch_btn.addClass('bt-disabled');
                        bt_select_batch_btn.find('.item').removeClass('active');
                    }
                }
                
            },

            /**
             * @description 渲染指定类型列内容
             * @param {object} data 渲染的数据
             * @param {object} rows 渲染的模板
             * @return void
            */
           $reader_column_type:function(item,rows){
                var value = rows[item.fid],event_list = {},className = '',config = [],_that = this;
                switch(item.type){
                    case 'text': //普通文本
                        config =  [value,event_list];
                    break;
                    case 'checkbox': //单选内容
                        config = ['<label><i class="cust—checkbox cursor-pointer checkbox_'+ this.random +'"></i><input type="checkbox" class="cust—checkbox-input"></label>',event_list];
                    break;
                    case 'password':
                        var _copy = '',_eye_open ='',className = 'ico_'+ _that.random +'_',html = '<span class="bt-table-password mr10"><i>**********</i></span>'
                        if(item.eye_open){
                            html += '<span class="glyphicon cursor pw-ico glyphicon-eye-open mr10 '+ className + 'eye_open" title="Show"></span>';
                            if(!event_list[className+'eye_open']) event_list[className+'eye_open'] = {type:'eye_open_password'};
                        }
                        if(item.copy){
                            html += '<span class="ico-copy cursor btcopy mr10 '+ className + 'copy" title="Copy"></span>'
                            if(!event_list[className+'copy']) event_list[className+'copy'] = {type:'copy_password'};
                        }
                        config = [html,event_list];
                    break;
                    case 'link': //超链接类型
                        className = 'click_'+ item.fid + '_' +this.random;
                        if(!event_list[className] && item.event) event_list[className] = {event:item.event,type:'rows'};
                        config = ['<a class="btlink '+ className +'" href="'+ (item.href?value:'javascript:;') +'" '+ (item.href?('target="'+ (item.target || '_blank')+'"'):'') +' title="'+ value +'">'+ value +'</a>',event_list];
                    break;
                    case 'input': //可编辑类型
                        blurName = 'blur_'+ item.fid + '_' +this.random;
                        keyupName = 'keyup_'+ item.fid + '_' +this.random;
                        if(!event_list[blurName] && item.blur) event_list[blurName] = {event:item.blur,eventType:'blur',type:'rows'};
                        if(!event_list[keyupName] && item.keyup) event_list[keyupName] = {event:item.keyup,eventType:'keyup',type:'rows'};
                        config = ['<input type="text" title="'+lan.site.click_edit+'"  class="table-input '+ blurName +' '+ keyupName  +'" value="'+ value +'">',event_list];
                    break;
                    case 'status': // 状态类型
                        var active = '';
                        className = 'click_'+ item.fid + '_' +this.random;
                        $.each(item.config.list,function(index,items){
                            if(items[0] === value) active = items;
                        });
                        if(!event_list[className] && item.event) event_list[className] = {event:item.event,type:'rows'};
                        config = ['<a class="btlink '+ className +' '+ (active[2].indexOf('#')>-1?'':active[2]) +'" style="'+ (active[2].indexOf('#')>-1?('color:'+active[2]+';'):'') +'" href="javascript:;"><span>'+ active[1] +'</span>'+ (item.config.icon?'<span class="glyphicon '+ active[3]+'"></span>':'') +'</a>',event_list];
                    break;
                    case 'switch': //开关类型
                        // config = ['<div></div>',event_list];
                    break;
                    case 'group':
                        var _html = '';
                        $.each(item.group,function(index,items){
                            className = (item.fid?item.fid:'group') + '_'+ index + '_' + _that.random;
                            if(items.template){
                                var _template = items.template(rows,_that),$template = $(_template);
                                if($template.length>0){
                                    _html += $template.addClass(className)[0].outerHTML
                                }else{
                                    _html += '<a href="javascript:;" class="btlink '+ className +'">'+ _template +'</a>';
                                }
                            }else{
                                _html += '<a href="javascript:;" class="btlink '+ className +'" '+ (items.hide?'style="display:none;"':'') +'>'+ items.title +'</a>';
                            }
                            _html += ((item.group.length - 1 != index)?'&nbsp;|&nbsp;':'')
                            if(!event_list[className] && items.event) event_list[className] = {event:items.event,type:'rows'};
                        });
                        config = [_html,event_list];
                    break;
                    default:
                        config =  [value,event_list];
                    break;
                }
                return config;
            },

            /**
             * @description 渲染工具条
             * @param {object} data 配置参数
             * @return void
            */
            $reader_tootls:function(config){
                var _that = this,event_list = {};
                /**
                 * @description 请求方法
                 * @param {Function} callback 回调函数
                 * @returns void 
                 */
                function request(active,check_list){
                    var loadT = bt.load(active.title +lan.site.executing),batch_config = {},
                    list = _that.$get_data_batch_list(active.paramId,check_list);
                    if(!active.beforeRequest){
                        batch_config[active.paramName] = list.join(',');
                    }else{
                        batch_config[active.paramName] = active.beforeRequest(check_list);
                    }
                    bt_tools.send({
                        url:active.url || _that.config.batch.url,
                        data:$.extend(active.param || {},batch_config)
                    },function(res){
                        loadT.close();
                        if(!res.status) return false;
                        if(typeof active.tips === 'undefined' || active.tips){
                            var html = '';
                            $.each(res.error,function(key,item){
                                html += '<tr><td><span>'+ key +'</span/></td><td><div style="float:right;" class="size_ellipsis"><span style="color:red">'+ item +'</span></div></td></tr>';
                            });
                            $.each(res.success,function(index,item){
                                html += '<tr><td><span>'+ item +'</span></td><td><div style="float:right;" class="size_ellipsis"><span style="color:#20a53a">'+lan.public.success+'</span></div></td></tr>';
                            });
                            _that.$batch_success_table({title:active.title,th:active.theadName,html:html});
                            _that.$refresh_table_list(true);
                        }
                        if(active.success){
                            active.success(res,check_list,_that);
                        }
                    });
                }
                /**
                 * @description 执行批量，包含递归批量和自动化批量
                 * @returns void
                 */
                function execute_batch(active,check_list,success){
                    if(active.callback){
                        active.callback({
                            loadT:0,
                            config:{},
                            check_list:check_list,
                            bacth_status:true,
                            start_batch:function(param,callback){
                                var _this = this;
                                if(active.load){
                                    this.loadT = layer.msg(lan.public.executeing+ active.title +'，<span class="batch_progress">'+lan.public.schedule+':0/'+ this.check_list.length +'</span>,'+lan.public.please_wait+ (active.clear?'<a href="javascript:;" class="btlink clear_batch" style="margin-left:20px;">cancel</a>':''),$.extend({icon:16,skin:'batch_tips',shade:.3,time:0},active.clear?{area:'420px'}:{}));
                                    $('#layui-layer'+_this.loadT).on('click','.clear_batch',function(){
                                        _this.clear_bacth();
                                    });
                                }
                                this.config = {param:param,url:active.url};
                                this.bacth(callback);
                            },
                            /**
                             * 
                             * @param {Number} index 递归批量程序
                             * @param {Function} callback 回调函数
                             * @return void(0)
                             */
                            bacth:function(index,callback){
                                var _this = this,param = {};
                                if(typeof index === "function") callback = index,index = 0;
                                if(index < this.check_list.length){
                                    if(typeof active.param == "function"){
                                        param = active.param(check_list[index]);
                                    }else{
                                        param = active.param;
                                    }
                                    this.config.param = $.extend(this.config.param,param);
                                    if(active.paramId)_this.config.param[active.paramId] = _this.check_list[index][active.paramId];
                                    if(this.config.param['bacth'] && index == this.check_list.length -1){
                                        delete this.config.param['bacth'];
                                    }
                                    if(!_this.bacth_status) return false;
                                    if(active.load) $('#layui-layer'+_this.loadT).find('.layui-layer-content').html('<i class="layui-layer-ico layui-layer-ico16"></i>'+lan.public.executeing+ active.title +'，<span class="batch_progress">'+lan.public.schedule+':'+ index +'/'+ _this.check_list.length +'</span>,'+lan.public.please_wait+ (active.clear?'<a href="javascript:;" class="btlink clear_batch" style="margin-left:20px;">cancel</a>':''));
                                    bt_tools.send({
                                        url:this.config.url,
                                        data:this.config.param,
                                        bacth:true,
                                    },function(res){
                                        $.extend(_this.check_list[index],{request:{status:typeof res.status === "boolean"?res.status:false,msg:res.msg || lan.public.request_error}});
                                        index++;
                                        _this.bacth(index,callback);
                                    });
                                }else{
                                    if(success) success();
                                    callback(this.check_list);
                                    layer.close(this.loadT);
                                }
                            },
                            clear_bacth:function(){
                                this.bacth_status = false;
                                layer.close(this.loadT);
                            }
                        });
                    }else{
                        if(!active.confirm){
                            if(active.confirmVerify){
                                bt.show_confirm(active.title+lan.public.in_bulk,active.title +lan.public.in_bulk+','+lan.public.risk_prompt,request)
                            }else{
                                bt.confirm({
                                    title:active.title+lan.public.in_bulk,
                                    msg:active.title+lan.public.in_bulk+','+lan.public.risk_prompt,
                                },function(){
                                    if(request) request(active,check_list)
                                });
                            }
                        }else{
                            request(active,check_list);
                        }
                    }
                }
                for(var i=0;i<config.length;i++){
                    var template = '',item = config[i];
                    switch(item.type){
                        case 'group':
                            $.each(item.list,function(index,items){
                                var _btn = item.type + '_' +_that.random +'_'+ index,html = '';
                                if(!items.group){
                                    template += '<button type="button" class="btn '+ (items.active?'btn-success':'btn-default') +' '+ _btn +' btn-sm mr5">'+ items.title +'</button>';
                                }else{
                                    template += '<div class="btn-group" style="vertical-align: top;">\
                                        <button type="button" class="btn btn-default '+ _btn +' btn-sm dropdown-toggle" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false"><span style="margin-right:2px;">'+lan.site.category_manager+'</span><span class="caret" style="position: relative;top: -1px;"></span></button>\
                                        <ul class="dropdown-menu"></ul>\
                                    </div>'
                                    if(item.list){
                                        $.each(item.list,function(index,items){
                                            html += '<li><a href="javascript:;" '+  +'>'+ items[item.key] +'</a></li>';
                                        });
                                    }
                                    if(items.init) setTimeout(function(){ items.init(_btn) },400); 
                                }
                                if(!event_list[_btn]) event_list[_btn] = {event:items.event,type:'button'};
                            });
                        break;
                        case 'search':
                            this.config.search = item;
                            var _input = 'search_input_'+this.random,_btn = 'search_btn_'+ this.random;
                            template = '<div class="bt_search"><input type="text" class="search_input '+ _input +'" style="'+ (item.width?('width:'+item.width):'') +'" placeholder="'+ (item.placeholder || '') +'"/><span class="glyphicon glyphicon-search '+ _btn +'" aria-hidden="true"></span></div>';
                            if(!event_list[_input]) event_list[_input] = {eventType:'keyup',type:'search_input'};
                            if(!event_list[_btn]) event_list[_btn] = {type:'search_btn'};
                        break;
                        case 'batch':
                            this.config.batch = item;
                            var batch_list = [],_html = '',active = item.config;
                            if(typeof item.config != 'undefined'){
                                _that.batch_active = active;
                                $(_that.config.el).on('click','.set_batch_option',function(e){
                                    var check_list =[];
                                    for(var i=0;i<_that.checkbox_list.length;i++){
                                        check_list.push(_that.data[_that.checkbox_list[i]]);
                                    }
                                    if($(this).hasClass('bt-disabled')){
                                        layer.tips(_that.config.batch.disabledTips || 'Select batch operation',$(this),{tips: [1,'red'],time: 2000});
                                        return false;
                                    }
                                    switch(typeof active.confirm){
                                        case 'function':
                                            active.confirm(active,function(param,callback){
                                                active.param = $.extend(active.param,param);
                                                execute_batch(active,check_list,callback);
                                            });
                                        break;
                                        case 'undefined':
                                            execute_batch(active,check_list);
                                        break;
                                        case 'object':
                                            var config = active.confirm;
                                            bt.open({
                                                title:config.title || 'Batch execute',
                                                area:config.area || '350px',
                                                btn:config.btn || ['Confirm','Cancel'],
                                                content:config.content,
                                                success:function(layero,index){
                                                    config.success(layero,index,active);
                                                },
                                                yes:function(index,layero){
                                                    config.yes(index,layero,function(param,callback){
                                                        active.param = $.extend(active.param,param);
                                                        request(active,check_list);
                                                    });
                                                }
                                            });
                                        break;
                                    }
                                });
                            }else{
                                $.each(item.selectList,function(index,items){
                                    if(items.group){
                                        $.each(items.group,function(indexs,itemss){
                                            batch_list.push($.extend({},items,itemss));
                                            _html += '<li class="item">'+ itemss.title +'</li>';
                                        });
                                        delete items.group;
                                    }else {
                                        batch_list.push(items);
                                        _html += '<li class="item">'+ items.title +'</li>';
                                    }
                                });
                                // 打开批量类型列表
                                $(_that.config.el).on('click','.bt_table_select_group .bt_select_value',function(e){
                                    var _this = this,$parent = $(this).parent(),bt_selects = $parent.find('.bt_selects'),area = $parent.offset(),_win_area = _that.$get_win_area();
                                    if($parent.hasClass('bt-disabled')){
                                        layer.tips(_that.config.batch.disabledSelectValue,$parent,{tips: [1,'red'],time: 2000})
                                        return false;
                                    }
                                    if($parent.hasClass('active')){
                                        $parent.removeClass('active');
                                    }else{
                                        $parent.addClass('active');
                                    }
                                    if(bt_selects.height() > (_win_area[1] - area.top)){ 
                                        bt_selects.addClass('top');
                                    }else{
                                        bt_selects.removeClass('top');
                                    }
                                    $(document).one('click',function(){
                                        $(_that.config.el).find('.bt_table_select_group').removeClass('active');
                                        return false;
                                    });
                                    return false;
                                });
                                // 选择批量的类型
                                $(_that.config.el).on('click','.bt_table_select_group .item',function(e){
                                    var _text = $(this).text(),_index = $(this).index();
                                    $(this).addClass('active').siblings().removeClass('active');
                                    $(_that.config.el +' .bt_select_tips').html(_text + lan.public.in_bulk+'<em>('+lan.site.have_been_selected+ _that.checkbox_list.length +')</em>');
                                    _that.batch_active = batch_list[_index];
                                    if(!_that.checked) $('.bt_table_select_group').removeClass('active');
                                });
                                // 执行批量操作
                                $(_that.config.el).on('click','.set_batch_option',function(e){
                                    var check_list = [],active = _that.batch_active;
                                    if($(this).hasClass('bt-disabled')){
                                        layer.tips(_that.config.batch.disabledSelectValue,$(this),{tips: [1,'red'],time: 2000});
                                        return false;
                                    }
                                    for(var i=0;i<_that.checkbox_list.length;i++){
                                        check_list.push(_that.data[_that.checkbox_list[i]]);
                                    }
                                    if(JSON.stringify(active) === '{}'){
                                        var bt_table_select_group = $(_that.config.el + ' .bt_table_select_group');
                                        layer.tips(lan.public.select_opt_type,bt_table_select_group,{tips:[1,'red'],time: 2000});
                                        bt_table_select_group.css('border','1px solid red');
                                        setTimeout(function(){
                                            bt_table_select_group.removeAttr('style');
                                        },2000);
                                        return false;
                                    }
                                    switch(typeof active.confirm){
                                        case 'function':
                                            active.confirm(active,function(param,callback){
                                                active.param = $.extend(active.param,param);
                                                execute_batch(active,check_list,callback);
                                            });
                                        break;
                                        case 'undefined':
                                            execute_batch(active,check_list);
                                        break;
                                        case 'object':
                                            var config = active.confirm;
                                            bt.open({
                                                title:config.title || lan.public.bulk_opt,
                                                area:config.area || '350px',
                                                btn:config.btn || [lan.public.confirm,lan.public.cancel],
                                                content:config.content,
                                                success:function(layero,index){
                                                    config.success(layero,index,active);
                                                },
                                                yes:function(index,layero){
                                                    config.yes(index,layero,function(param,callback){
                                                        active.param = $.extend(active.param,param);
                                                        request(active,check_list);
                                                    });
                                                }
                                            });
                                        break;
                                    }
                                });
                            }
                            // template = '<div class="bt_batch "><label><i class="cust—checkbox cursor-pointer checkbox_'+ this.random +'" data-checkbox="all"></i><input type="checkbox" lass="cust—checkbox-input" /></label><div class="bt_table_select_group bt_disabled not-select"><span class="bt_select_value"><span class="bt_select_tips">'+lan.public.select_opt_type+'<em></em></span><span class="glyphicon glyphicon-triangle-bottom ml5"></span></span><ul class="bt_selects ">'+ _html +'</ul></div><button class="btn btn-success btn-sm set_batch_option bt-disabled" >'+ item.buttonValue +'</button></div>';
                            template = '<div class="bt_batch"><label><i class="cust—checkbox cursor-pointer checkbox_'+ this.random +'" data-checkbox="all"></i><input type="checkbox" lass="cust—checkbox-input" /></label>'+ (typeof item.config != 'undefined'?'<button class="btn btn-default btn-sm set_batch_option bt-disabled">'+ item.config.title +'</button>':'<div class="bt_table_select_group bt-disabled not-select"><span class="bt_select_value"><span class="bt_select_tips">'+lan.public.select_opt_type+'<em></em></span><span class="glyphicon glyphicon-triangle-bottom ml5"></span></span><ul class="bt_selects ">'+ _html +'</ul></div><button class="btn btn-default btn-sm set_batch_option bt-disabled" >'+ item.buttonValue +'</button>') +'</div>';
                        break;
                        // case 'batch_btn':
                        //     _that.batch = item;
                        //     $(_that.config.el).on('click','.set_batch_option',function(e){
                        //         var check_list = [],active = {},index = $(this).index()-1;
                        //         _that.batch_active = _that.batch.selectList[index];
                        //         active = _that.batch_active;
                        //         if($(this).hasClass('bt-disabled')){
                        //             layer.tips(_that.batch.disabledSelectValue,$(this),{tips: [1,'red'],time: 2000});
                        //             return false;
                        //         }
                        //         for(var i=0;i<_that.checkbox_list.length;i++){
                        //             check_list.push(_that.data[_that.checkbox_list[i]]);
                        //         }
                        //         switch(typeof active.confirm){
                        //             case 'function':
                        //                 active.confirm(active,function(param,callback){
                        //                     active.param = $.extend(active.param,param);
                        //                     execute_batch(active,check_list,callback);
                        //                 });
                        //             break;
                        //             case 'undefined':
                        //                 execute_batch(active,check_list);
                        //             break;
                        //             case 'object':
                        //                 var config = active.confirm;
                        //                 bt.open({
                        //                     title:config.title || lan.public.exec,
                        //                     area:config.area || '350px',
                        //                     btn:config.btn || [lan.public.confirm,lan.public.cancel],
                        //                     content:config.content,
                        //                     success:function(layero,index){
                        //                         config.success(layero,index,active);
                        //                     },
                        //                     yes:function(index,layero){
                        //                         config.yes(index,layero,function(param,callback){
                        //                             active.param = $.extend(active.param,param);
                        //                             request(active,check_list);
                        //                         });
                        //                     }
                        //                 });
                        //             break;
                        //         }
                        //     });
                        //     template = '<div class="bt_batch "><label><i class="cust—checkbox cursor-pointer checkbox_'+ this.random +'" data-checkbox="all"></i><input type="checkbox" lass="cust—checkbox-input" /></label><button class="btn btn-success btn-sm set_batch_option bt-disabled">'+lan.public.exec+'</button></div>';
                        // break;
                        case 'page':
                            this.config.page = item;
                            var pageNumber = bt.get_cookie(this.config.cookiePrefix+'_'+ this.config.page.numberParam);
                            if(this.config.cookiePrefix && pageNumber) this.config.page.number = pageNumber;
                            template = this.$reader_page(this.config.page,'<div><span class="Pcurrent">1 </span><span class="Pcount">'+lan.public_backup.total+'</span></div>');
                        break;
                    }
                    if(template){
                        var tools_group = $(_that.config.el + ' .tootls_'+ item.positon[1]);
                        if(tools_group.length){
                            var tools_item = tools_group.find('.pull-'+ item.positon[0]);
                            tools_item.append(template);
                        }else{
                            var tools_group_elment = '<div class="tootls_group tootls_'+ item.positon[1] +'"><div class="pull-left">'+ (item.positon[0]=='left'?template:'') +'</div><div class="pull-right">'+ (item.positon[0]=='right'?template:'') +'</div></div>';
                            if(item.positon[1] === 'top'){
                                $(_that.config.el).append(tools_group_elment);
                                if($(_that.config.el +' .divtable').length === 0) $(_that.config.el).append('<div class="divtable mtb10"></div>');
                            }else{
                                if($(_that.config.el +' .divtable').length === 0) $(_that.config.el).append('<div class="divtable mtb10"></div>');
                                $(_that.config.el).append(tools_group_elment);
                            }
                        }
                    }
                }
                if(!this.init) this.$event_bind(event_list);
            },

            /**
             * @description 获取数据批量列表
             * @param {string} 需要获取的字段
             * @return {array} 当前需要批量列表
            */
            $get_data_batch_list:function(fid,data){
                var arry = [];
                $.each(data || this.data,function(index,item){
                    arry.push(item[fid])
                });
                return arry;
            },

            /**
             * @description 渲染分页
             * @param {object} config 配置文件
             * @param {object} page 分页
             * @return void
             */
            $reader_page:function(config,page){
                var _that = this,$page = $(page),template = '',eventList = {};
                $page.find('a').addClass('page_link_'+ this.random);
                template += $page.html();
                if(config.numberStatus){
                    var className = 'page_select_'+ this.random;
                    template += '<select class="page_select_number '+ className +'">';
                    $.each(config.numberList,function(index,item){
                        template+= '<option value="'+ item +'" '+ (config.number == item?'selected':'') +'>'+ item +lan.site.items_page+'</option>';
                    });
                    template += '</select>';
                    eventList[className] = {eventType:"change",type:'page_select'};
                }
                if(config.jump){
                    var inputName = 'page_jump_input-'+ this.random;
                    var btnName = 'page_jump_btn_'+ this.random;
                    template += '<div class="page_jump_group"><span class="page_jump_title">'+lan.public.jump_to_page+'</span><input type="number" class="page_jump_input '+ inputName +'" value="'+ config.page +'" /><span class="page_jump_title"></span><button type="button" class="page_jump_btn '+ btnName +'">'+lan.public.confirm+'</button></div>'
                    eventList[inputName] = {eventType:'keyup',type:'page_jump_input'};
                    eventList[btnName] = {type:'page_jump_btn'};
                }
                eventList['page_link_'+ this.random] = {type:'cut_page_number'};
                _that.config.page.total = parseInt($page.find('.Pcount').html().match(/([0-9]*)/g)[1]);
                _that.$event_bind(eventList);
                return '<div class="page">'+ template +'</div>';
            },

            /**
             * @deprecated 动态处理合并行内，css样式
             * @param {object} rows 当前行数据
             * @return {stinrg} className class类名
             * @return void
            */
            $dynamic_merge_style:function(column,index){
                var str = '';
                $.each(column,function(key,item){
                    switch(key){
                        case 'align':
                            str += 'text-align:'+ item +';';
                        break;
                        case 'width':
                            str += 'width:'+ (typeof item == 'string'?item:item +'px') +';';
                        break;
                        case 'style':
                            str += item;
                        break;
                        case 'minWidth':
                            str += 'min-width:'+ (typeof item == 'string'?item:item +'px') +';';
                        break;
                        case 'maxWidth':
                            str += 'max-width:'+ (typeof item == 'string'?item:item +'px') +';';
                        break;
                    }
                });
                return {index:index,css:str};
            },

            /**
             * @description 事件绑定
             * @param {array} eventList 事件列表
             * @return void
             */
            $event_bind:function(eventList){
                var _that = this;
                $.each(eventList,function(key,item){
                    if(_that.event_list[key] && _that.event_list[key].eventType === item.eventType) return true;
                    _that.event_list[key] = item;
                    $(_that.config.el).on(item.eventType || 'click','.'+ key,function(ev){
                        var index = $(this).parents('tr').index(),data1 = $(this).data(),arry = [];
                        switch(item.type){
                            case 'rows':
                                _that.event_rows_model = {
                                    el:$(this),
                                    model:_that.config.column[$(this).parents('td').index()],
                                    rows:_that.data[index],
                                    index:index
                                }
                                arry = [_that.event_rows_model.rows,_that.event_rows_model.index,ev,key,_that];
                            break;
                            case 'sort':
                                var model = _that.config.column[data1.index];
                                if($(this).hasClass('sort-active')) $('.sort_'+ _that.random + ' .sort-active').data({'sort':'desc'});
                                $('.sort_'+ _that.random).removeClass('sort-active').find('.glyphicon').removeClass('glyphicon-triangle-top').addClass('glyphicon-triangle-bottom');
                                $(this).addClass('sort-active');
                                if(data1.sort == 'asc'){
                                    $(this).data({'sort':'desc'});
                                    $(this).find('.glyphicon').removeClass('glyphicon-triangle-top').addClass('glyphicon-triangle-bottom');
                                }else{
                                    $(this).data({'sort':'asc'});
                                    $(this).find('.glyphicon').removeClass('glyphicon-triangle-bottom').addClass('glyphicon-triangle-top');
                                }
                                _that.config.sort = _that.config.sortParam({name:model.fid,sort:data1.sort})
                                _that.$refresh_table_list(true);
                            break;
                            case 'checkbox':
                                var all = $(_that.config.el + ' [data-checkbox="all"]'),checkbox_list = $(_that.config.el +' tbody .checkbox_'+_that.random);
                                if(data1.checkbox == undefined){
                                    if(!$(this).hasClass('active')){
                                        $(this).addClass('active');
                                        _that.checkbox_list.push(index);
                                        if(_that.data.length === _that.checkbox_list.length){
                                            all.addClass('active').removeClass('selected')
                                        }else if(_that.checkbox_list.length > 0){
                                            all.addClass('selected');
                                        }
                                    }else{
                                        $(this).removeClass('active');
                                        _that.checkbox_list.splice(_that.checkbox_list.indexOf(index),1);
                                        if(_that.checkbox_list.length > 0){
                                            all.addClass('selected').removeClass('active');
                                        }else{
                                            all.removeClass('selected active');
                                        }
                                    }
                                }else{
                                    if(_that.checkbox_list.length === _that.data.length){
                                        _that.checkbox_list = [];
                                        checkbox_list.removeClass('active selected').next().prop('checked','checked')
                                        all.removeClass('active');
                                    }else{
                                        checkbox_list.each(function(index,item){
                                            if(!$(this).hasClass('active')){
                                                $(this).addClass('active').next().prop('checked','checked');
                                                _that.checkbox_list.push(index);
                                            }
                                        });
                                        all.removeClass('selected').addClass('active');
                                    }
                                }
                                _that.$set_batch_view();
                            break;
                            case 'button':
                                arry.push(ev,_that);
                            break;
                            case 'search_focus':
                                var search_tips = $(_that.config.el+' .bt_search_tips');
                                if($(_that.config.el + ' .bt_search_tips').length > 0){
                                    search_tips.remove();
                                }
                            break;
                            case 'search_input':
                                if(ev.keyCode == 13){
                                    $(_that.config.el +' .search_btn_'+ _that.random).click();
                                    return false;
                                }
                            break;
                            case 'search_btn':
                                var _search = $(_that.config.el+' .search_input'),val = $(_that.config.el+' .search_input').val();
                                _that.config.search.value = val;
                                _search.append('<div class="bt_search_tips"><span>'+ val +'</span><i class="bt_search_close"></i></div>');
                                _that.$refresh_table_list(true);
                            break;
                            case 'page_select':
                                var limit = parseInt($(this).val());
                                _that.config.page.number = limit;
                                _that.config.page.page = 1;
                                _that.$refresh_table_list(true);
                                return false;
                            break;
                            case 'page_jump_input':
                                if(ev.keyCode == 13){
                                    $(_that.config.el +' .page_jump_btn_'+ _that.random).click();
                                    $(this).focus();
                                }
                                return false;
                            break;
                            case 'page_jump_btn':
                                var jump_page = parseInt($(_that.config.el +' .page_jump_input-'+ _that.random).val()),max_number = Math.ceil(_that.config.page.total/ _that.config.page.number);
                                if(jump_page > max_number) jump_page = _that.config.page.page;
                                _that.config.page.page = jump_page;
                                _that.$refresh_table_list(true);
                            break;
                            case 'cut_page_number':
                                var page = parseInt($(this).attr('href').match(/([0-9]*)$/)[0])
                                _that.config.page.page = page;
                                _that.$refresh_table_list(true);
                                return false;
                            break;
                            case 'eye_open_password':
                                if($(this).hasClass('glyphicon-eye-open')){
                                    $(this).addClass('glyphicon-eye-close').removeClass('glyphicon-eye-open');
                                    $(this).prev().text(_that.data[index].password);
                                }else{
                                    $(this).addClass('glyphicon-eye-open').removeClass('glyphicon-eye-close');
                                    $(this).prev().html('<i>**********</i>');
                                }
                                return false;
                            break;
                            case 'copy_password':
                                bt.pub.copy_pass(_that.data[index].password);
                                return false;
                            break;
                        }
                        if(item.event) item.event.apply(this,arry);
                    });
                });
            },

            /**
             * @description 样式绑定
             * @param {array} style_list 样式列表
             * @return void
             */
            $style_bind:function(style_list,status){
                var str = '',_that = this;
                $.each(style_list,function(index,item){
                    if(item.css != ''){
                        if(!item.className){
                            str += _that.config.el +' thead th:nth-child('+ (item.index + 1) +'),'+ _that.config.el+' tbody tr td:nth-child'+ (item.span?' span':'') +'('+ (item.index + 1) +'){'+ item.css +'}'
                        }else{
                            str += item.className + '{'+ item.css +'}';
                        }
                    }
                });
                if($('#bt_table_'+ _that.random ).length == 0) $(_that.config.el).append('<style type="text/css" id="bt_table_'+ _that.random +'">'+ str +'</style>');
            },

            /**
             * @deprecated 获取WIN高度或宽度
             * @returns 返回当期的宽度和高度
            */
            $get_win_area:function(){
                return [window.innerWidth,window.innerHeight];
            },
            
            /**
             * @description 请求数据，
             * @param {object} param 参数和请求路径
             * @return void
            */
            $http:function(success){
                var param = {},config = this.config,_page = config.page,_search = config.search,_sort = config.sort || {};
                if(_page){ 
                    param[_page.numberParam] = _page.number,param[_page.pageParam] = _page.page;
                    if(this.config.cookiePrefix) bt.set_cookie(this.config.cookiePrefix+'_'+ _page.numberParam,_page.number);
                }
                if(_search) param[_search.searchParam] = _search.value;
                if(this.config.beforeRequest) config.param = this.config.beforeRequest(config.param);
                bt_tools.send({
                    url:config.url,
                    data:$.extend(config.param,param,_sort),
                },function(res){
                    if(config.dataFilter){
                        var data = config.dataFilter(res);
                        if(success) success(data.data,data.page);
                    }else {
                        if(success) success(res.data,res.page);
                    }
                });
            }
        }
        return new ReaderTable(config);
    },
    /**
     * @description 选择文件目录
     * @param {object|string} data 当前 {path:[string] 选择路径,title:[string] title标题,ext:[array]限制的文件类型}，或选择目录地址，可以为空,为空这默认使用当前目录作为选择目录
     * @param {function} 回调函数，选择完成后的操作
     * @return void
    */
    select_file:function(data,callback){
        if(typeof data === 'string') data = {path:data,type:2,title:lan.public.select_fileordir,ext:[],limit:''};
        if(typeof data === 'function') type = callback,callback = data,data = {path:bt.get_cookie('Path')};
        if(typeof type !== 'number') type = 0;
        var that = this,select_file = {
            type:type,
            type_tips:type == 0?lan.public.dir:(type == 1?lan.site.file:lan.public.fileordir),
            select_list:[],
            select_path:bt.get_cookie('Path') || (bt.os == 'Windows'?setup_path:'/www/wwwroot'),
            select_config:{},
            scroll_width:0,
            reader_view:function(){
                var _this = this;
                this.scroll_width = select_file.getScrollbarWidth();
                layer.open({
                    type:1,
                    title: data.title || (lan.public.select + _this.type_tips),
                    shadeClose:false,
                    closeBtn:1,
                    area:['650px','550px'],
                    content:'<div id="select_file_style"></div><div id="select_file_directory" class="select_file_content"><div class="file_path_views"><div class="forward_path"><span class="active" title="'+lan.public.back+'"><i class="iconfont icon-arrow-lift"></i></span><span class="active" title="'+lan.public.next+'"><i class="iconfont icon-arrow-right"></i></span><span class="file_return_level" title="'+lan.public.return+'"><i class="iconfont icon-prev"></i></span></div><div class="file_path_input"><div class="file_path_shadow"></div><div class="file_dir_view" data-width="244"></div><input type="text" data-path="C:/BtSoft/backup" class="path_input"></div><div class="file_path_refresh" title="'+lan.public.fresh+'"><i class="iconfont icon-shuaxin"></i></div><div class="search_path_views"><input type="text" placeholder="'+lan.public.search_file_name+'" class="file_search_input"><button type="submit" class="path_btn"><i class="iconfont icon-search"></i></button></div></div><div class="select_file_tootls"><button type="button" class="select_btn">'+lan.bt.adddir+'</button></div><div class="select_file_body"><div class="select_mount_list not-select" id="select_mount_list"></div><div class="select_dir_list not-select"><div class="select_list_thaed"><table class="mask_thead"><thead><tr><th data-type="filename"><span>'+lan.public.name+'</span><i class="iconfont icon-xiala"></i><i class="icon-drag"></i></th><th data-type="mtime"><span>'+lan.public.modify_time+'</span><i class="iconfont icon-xiala"></i><i class="icon-drag"></i></th><th data-type="type" class="active"><span>'+lan.site.redirect_type+'</span><i class="iconfont icon-xiala"></i><i class="icon-drag"></i></th></tr></thead></table><div class="select_list_shadow"></div></div><div class="select_list_body"><table><thead><tr><th><span>文件</span><i></i></th><th><span>修改时间</span><i></i></th><th><span>类型</span><i></i></th></tr></thead><tbody id="select_dir_list"></tbody></table></div></div></div><div class="select_file_group"><div class="select-line"><span class="select-line-name">'+ _this.type_tips +'名:</span><div class="select-line-content"><input type="text" name="select_name" class="file_directory" /></div></div><div class="select_btn_group"><button class="btn btn-success btn-sm" type="button">选择'+  _this.type_tips +'</button><button class="btn btn-default btn-sm" type="button">取消</button></div></div></div>',
                    success:function(){
                        _this.evnet_bind();
                        _this.render_file_list(function(){
                            _this.set_path_width();
                        });
                        $('.select_list_thaed').css('right',_this.scroll_width+'px');
                    }
                });
            },
            /**
             * @description 事件绑定
            */
            evnet_bind:function(){
                var _this = this;
                $('#select_dir_list').on('click','tr',function(){
                    var index = $(this).data('index');
                    $(this).addClass('active').siblings().removeClass('active');
                    $('[name="select_name"]').val(_this.select_list[index].filename);
                });
                $('.select_list_body').on('scroll',function(e){
                    var top = $(this).scrollTop(),left = $(this).scrollLeft();
                    if(top > 0){
                        $('.select_list_shadow').show();
                    }else{
                        $('.select_list_shadow').hide();
                    }
                    if(left >= 0){
                        $('.select_list_thaed').css('left',(4-left ) +'px');
                    }
                    e.stopPropagation();
                    e.preventDefault();
                });
                $('.file_path_refresh').on('click',function(){
                    _this.render_file_list();
                });
                $('.select_dir_list thead th .icon-drag').on('mousedown',function(ev){
                    var x = ev.clientX,th = $(this).parent(),th_index = th.index(),th_width = th[0].clientWidth,min_width = parseInt($(this).parent().attr('data-min')),timeOut = null;
                    if(ev.which === 1){
                        var document_mousemove = function(e){
                            var move_x = e.clientX,offset_x = move_x - x,_width = th_width + offset_x;
                            timeOut = setTimeout(function(){
                                _this.set_select_width(th_index,'width:'+_width+'px');
                            },0);
                        },
                        document_mouseup = function(){
                            $(this).unbind(document_mousemove);
                            $(this).unbind(document_mouseup);
                        };
                        $(document).on('mousemove',document_mousemove).one('mouseup',function(){
                            $(this).unbind(document_mousemove);
                            $(this).unbind(this);
                        })
                    }
                    ev.stopPropagation();
                });
                $('.select_dir_list thead th>span').on('click',function(ev){
                    var th = $(this).parent(),type = th.data('type'),is_active = th.hasClass('active'),is_sort = th.hasClass('sort');
                    if(is_active){
                        th.addClass('sort').removeClass('active');
                    }else if(is_sort){
                        th.addClass('active').removeClass('sort');
                    }else{
                        th.addClass('active');
                    }
                    th.siblings().removeClass('active sort');
                    _this.render_file_list({sort:type,reverse:is_active?1:0});
                    ev.stopPropagation();
                });
                $('.search_path_views input').on('keyup',function(){
                    var val = $(this).val();
                });
            },
            /**
             * @description 设置当前路径宽度
             * @param {}
            */
            set_path_width:function(width){
                var _width = 0,_dir_view = $('.file_dir_view')[0].offsetWidth,_item  = $('.file_dir_view .file_dir_item'),_arry = [],_width =0;
                $('.file_dir_view .file_dir_item').each(function(){
                    _arry.push($(this)[0].offsetWidth);
                });
                var arry = _arry.reverse();
                for(var i=0;i<arry.length;i++){
                    _width+= arry[i];
                    if(_dir_view - _width <= 60){
                        $('.file_dir_omit').removeClass('hide').find('.nav_down_list').html($('.file_dir_view .file_dir_item:lt('+ i +')'));
                        $('.file_dir_view .file_dir_item').show();
                        $('.file_dir_view .file_dir_item:lt('+ i +')').hide();
                        return false;
                    }
                }
            },
            /**
             * @description 渲染文件列表
             * @param {object} data 配置参数，包含path路径、serarch搜索字段
            */
            render_file_list:function(data,callback){
                var mount_html = '',dir_html = '',_this = this,datas = {path:this.select_path,sort:'type',disk:true};
                if(typeof data == "undefined") data = datas;
                if(typeof data == "function") callback = data,data = datas;
                _this.select_config = $.extend(datas,data);
                that.send({url:'/files?action=GetDir',data:_this.select_config},function(rdata){
                    var dir_list = rdata.DIR,files_list = rdata.FILES,disk_list = rdata.DISK,arry = [];
                    $.each(files_list,function(key,item){
                        var _list = item.split(';'),ext = _list[0].split('.'),time = bt.format_data(_list[2]);
                        arry.push({type:'file',filename:_list[0],ext:ext[ext.length-1],size:_list[1],accept:_list[3],mtime:time});
                    });
                    $.each(dir_list,function(key,item){
                        var _list = item.split(';'),time = bt.format_data(_list[2]);
                        arry.push({type:'dir',filename:_list[0],size:_list[1],accept:_list[3],mtime:time});
                    });
                    _this.select_list = arry;
                    _this.render_path_list(rdata.PATH);
                    $.each(disk_list,function(index,item){
                        var name = (item.path == '/'?'根目录':item.path.indexOf(':/') > -1?('本地磁盘('+ item.path.match(/[A-Z]+/)[0])+ ':)':item.path)
                        mount_html += '<div class="item" data-menu="'+ item.path +'" title="名称:&nbsp;'+ name +'\n路径:&nbsp;'+ item.path +'\n总容量:&nbsp;'+ item.size[0] +'\n可用容量:&nbsp;'+ item.size[2] +'">'+
                            '<span class="glyphicon glyphicon-hdd mr5"></span>'+
                            '<span>'+ name +'</span>'+
                        '</div>';
                    });
                    $.each(arry,function(index,item){
                        var mtime = bt.format_data(item.mtime),type = (item.type == 'dir'?'文件夹':'文件');
                        dir_html += '<tr data-index="'+ index +'" title="名称：'+ item.filename +'\r修改时间:'+ mtime +'\r类型：'+ type +'">\
                            <td><span><i class="'+ item.type +'-icon"></i><span>'+ item.filename +'</span></span></td>\
                            <td><span>'+ mtime +'</span></td>\
                            <td><span>'+ (item.type == 'dir'?'文件夹':'文件') +'</span></td>\
                        </tr>';
                    });
                    $('#select_mount_list').html(mount_html);
                    $('#select_dir_list').html(dir_html);
                    if(callback) callback(rdata);
                });
            },
            /**
             * @description 渲染路径列表
             * @param {Function} callback 回调函数
             * @return void
            */
            render_path_list:function(path,callback){
                var html = '<div class="file_dir_omit hide" title="展开已隐藏的目录"><span></span><i class="iconfont icon-zhixiang-zuo"></i><div class="nav_down_list"></div></div>', path_before = '',dir_list = path.split("/").splice(1),first_dir = path.split("/")[0];
                if(bt.os === 'Windows'){
                    if(dir_list.length == 0) dir_list = [];
                    dir_list.unshift('<span class="glyphicon glyphicon-hdd"></span><span class="ml5">本地磁盘('+ first_dir +')</span>');
                }else{
                    if(path == '/') dir_list = [];
                    dir_list.unshift('根目录');
                }
                for(var i = 0; i < dir_list.length; i++){
                    path_before += '/' + dir_list[i];
                    if (i == 0) path_before = '';
                    html += '<div class="file_dir_item">\
                        <span class="file_dir" title="' + (first_dir + path_before) + '">' + dir_list[i] + '</span>\
                        <i class="iconfont icon-arrow-right"></i>\
                        <ul class="nav_down_list">\
                            <li data-path="*"><span>加载中</span></li>\
                        </ul>\
                    </div>';
                }
                $('.path_input').val('').attr('data-path',path);
                var file_dir_view = $('#select_file_directory .file_path_input .file_dir_view');
                file_dir_view.html(html);
                if(callback) callback(path);
            },

            /**
             * @description 设置标题宽度
             * @param {string} th_index 表头序列号
             * @param {string} style class样式
            */
            set_select_width:function(th_index,style){
                var _this = this,className = '.select_dir_list tbody td:nth-child('+ (th_index+1) +')>span,.select_dir_list thead th:nth-child('+ (th_index+1) +')>span',style_index = $('#th-index-'+th_index);
                if(style_index.length > 0){
                    style_index.html(className +'{'+ style +'}');
                }else{
                    $('#select_file_style').append('<style type="text/css" id="th-index-'+ th_index +'">'+ className +'{'+ style +'}' +'</style>');
                }
            },
            /**
             * @description 样式转换文件样式
             * @param {string} style 样式
             */
            cut_style_object:function(style){
                var object = {},arry = style.split(';');
                return object;
            },
            /**
             * @description 获取滚动条宽度
             */
            getScrollbarWidth:function() {
                var odiv = document.createElement('div'),//创建一个div
                    styles = {
                        width: '100px',
                        height: '100px',
                        overflowY: 'scroll'//让他有滚动条
                    }, i, scrollbarWidth;
                for (i in styles) odiv.style[i] = styles[i];
                document.body.appendChild(odiv);//把div添加到body中
                scrollbarWidth = odiv.offsetWidth - odiv.clientWidth;//相减
                odiv.remove();//移除创建的div
                return scrollbarWidth;//返回滚动条宽度
            }
        }
        select_file.reader_view();
    },
    
    /**
     * @description 渲染Form表单
     * @param {*} config 
     * @return 当前实例对象
     */
    form:function(config){
        var _that = this;
        function ReaderForm(config){
            this.config = config;
            this.$load();
        }
        ReaderForm.prototype = {
            element:null,
            style_list:[], // 样式列表
            event_list:{}, // 事件列表,已绑定事件
            event_type:['click','event','focus','keyup','blur','change',],
            hide_list:[],
            form_element:{},
            form_config:{},
            random:bt.get_random(5),
            $load:function(){
                var that = this;
                if(that.el){
                    this.$reader_content(function(){
                        that.$event_bind();
                    });
                }
            },
            /**
             * @description 激活焦点
             * @param {Function} callback 回调函数
             * @returns void
             */
            $active_focus:function(callback,condition){
                var _that = this;
                $('.input_checked_'+ _that.random).focus();
                this.checked_blur = function(ev){
                    setTimeout(function(){
                        if(condition){
                            $('.input_checked_'+ _that.random).focus();
                            return false;
                        }
                        if(callback) callback(ev);
                        delete _that.checked_blur;
                    },200);
                }
            },

            /**
             * @description 渲染Form内容
             * @param {Function} callback 回调函数
             */
            $reader_content:function(callback){
                var that = this,html = '',_content = '',event_list = {};
                $.each(that.config.form,function(index,item){
                    html += that.$reader_content_row(index,item);
                });
                that.element = $('<form class="bt-form" data-form="'+ that.random +'">'+ html +'</form>');
                _content = $('<div class="'+ _that.$verify(that.config.class) +'"><input type="checkbox" class="blur_checked input_checked_'+ that.random +'"></div>');
                _content.append(that.element);
                event_list['input_checked_'+ that.random] = {'focus':{type:'input_checked',onEvent:false,
                    event:function(ev,that){
                        that.checked = true;
                        return false;
                    }
                },'blur':{type:'input_checked',onEvent:false,event:function(ev,that){
                    that.checked = false;
                    if(that.checked_blur) that.checked_blur(ev);
                    }
                }}
                $.extend(that.event_list,event_list);
                if(callback) callback();
                return _content[0].outerHTML;
            },

            /**
             * @description 渲染行内容
             * @param {object} data Form数据
             * @param {number} index 下标
             * @return {string} HTML结构
             */
            $reader_content_row:function(index,data){
                var that = this,help = data.help;
                return '<div class="line'+ _that.$verify(data.class) + _that.$verify(data.hide,'hide',true) +'"'+ _that.$verify(data.id,'id') +'>'+
                    (data.label?'<span class="tname">'+ data.label +'</span>':'') +
                    '<div class="'+ (data.label?'info-r':'') + _that.$verify(data.line_class) +'"'+ _that.$verify(that.$reader_style(data.line_style),'style') +'>'
                        + that.$reader_form_element(data.group,index)
                        + (help?('<div class="c9 mt5 '+ _that.$verify(help.class,'class') +'" '+ _that.$verify(that.$reader_style(help.style),'style') +'>'+ help.list.join('</br>') +'</div>'):'')
                    +'</div>'
                +'</div>';
            },
            
            /**
             * @description 渲染form类型
             * @param {object} data 表单数据
             * @param {number} index 下标
             * @return {string} HTML结构
            */
            $reader_form_element:function(data,index){
                var that = this,config = [],html = '',event_list = {};
                if(!Array.isArray(data)) data = [data];
                $.each(data,function(key,item){
                    var style = that.$reader_style(item.style) + _that.$verify(item.width,'width','style'),
                        attribute = that.$verify_group(item,['name','value','placeholder','disabled','readonly','autofocus','autocomplete','min','max']),
                        event_group = that.$create_event_config(item),
                        eventName = '';
                        html += item.label?'<span class="mr5">'+ item.label +'</span>':'';
                    if(typeof item['name'] !== "undefined") event_list[item.name] = event_group;
                    switch(item.type){
                        case 'text': // 文本选择
                        case 'checkbox': // 复选框
                        case 'password': // 密码
                        case 'radio': // 单选框
                        case 'number': // 数字
                            var _event = 'event_'+ item.name  +'_'+ that.random,is_checkbox = item.type === 'checkbox'?true:false;
                            if(item.type === 'radio'){
                                $.each(item.label_tips,function(index,items){
                                    if(item.block) html += '<div class="block '+ (item.block_class?item.block_class:'') + '">';
                                    html += '<input type="'+ item.type +'"'+ attribute +' '+ (item.icon?'id="'+ _event +'"':'') +' class="bt-input-'+ (item.type != 'select_path'?item.type:'text') +' mr10 '+ (item.label?'form_middle':'') + _that.$verify(item.class,'class') +'"'+ _that.$verify(style,'style') +' '+ (is_checkbox?'id="'+ that.random +'_'+ item.name +'"':'') +' '+(index == 0?'checked':'')+' id="'+ that.random +'_'+ item.name + index +'"/>';
                                    html += '<label for="'+ that.random +'_'+ item.name + index +'">'+ items +'</label>';
                                    if(item.block) html += '</div>';
                                })
                            }else{
                                if(item.block) html += '<div class="block ' + (item.hide?'hide':'') +' '+ (item.block_class?item.block_class:'') + '">';
                                html += '<input type="'+ item.type +'"'+ attribute +' '+ (item.icon?'id="'+ _event +'"':'') +' class="bt-input-'+ (item.type != 'select_path'?item.type:'text') +' mr10 '+' '+_event+ (item.label?'form_middle':'') + _that.$verify(item.class,'class') +'"'+ _that.$verify(style,'style') +' '+ (is_checkbox?'id="'+ that.random +'_'+ item.name +'"':'') +'/>';
                                if(item.type == 'checkbox')  html += '<label for="'+ that.random +'_'+ item.name +'">'+ item.label_tips +'</label>';
                                if(item.block) html += '</div>';
                                that.event_list[_event] = {'click':{event:item.event}}
                            }
                            if(item.icon){
                                html += '<span class="glyphicon '+ item.icon.type +' '+ item.name +'_icon cursor" '+ _that.$verify(that.$reader_style(item.icon.style),'style') +'></span>';
                                event_list[item.name+'_icon'] = {'click':{type:'select_path',config:item}};
                            }
                        break;
                        case 'textarea':
                            html += '<textarea class="bt-input-text"'+ _that.$verify(style,'style') + attribute +' >'+ (item.value || '') +'</textarea>';
                            $.each(['blur','focus','input'],function(index,items){
                                if(item.tips){
                                    var added = null;
                                    switch(items){
                                        case 'blur':
                                            added = function(ev,item){
                                                if($(this).val() === '') $(this).next().show();
                                                layer.close(item.tips.loadT);
                                            }
                                        break;
                                        case 'focus':
                                            added = function(ev,item){
                                                $(this).next().hide();
                                                item.tips.loadT = layer.tips(tips,$(this),{tips:[1,'#20a53a'],time:0,area:$(this).width()})
                                            }
                                        break;
                                    }
                                }
                                event_list[item.name][items]?(event_list[item.name][items]['added'] = added):(event_list[item.name][items] = {type:item.type,cust:false,event:item[items],added:added});
                            });
                            if(item.tips){
                                var tips = '';
                                if(typeof item.tips.list === "undefined"){
                                    tips = item.tips.text;
                                }else{
                                    tips = item.tips.list.join('</br>');
                                }
                                html += '<div class="placeholder c9 '+ item.name +'_tips" '+ _that.$verify(that.$reader_style(item.tips.style),'style') +'>'+ tips +'</div>';
                                event_list[item.name+'_tips'] = {'click':{type:'textarea_tips',config:item}};
                            }
                        break;
                        case 'select':
                            html += that.$reader_select(item,style,attribute,index);
                            that.event_list['custom_select'] = {'click':{type:'custom_select',children:'.bt_select_value'}};
                            that.event_list['custom_select_item'] = {'click':{type:'custom_select_item',children:'li.item'}};
                        break;
                        case 'link':
                            eventName = 'event_' + bt.get_random(6);
                            html += '<a href="'+ (item.href || 'javascript:;') +'" class="btlink offsetY7'+ _that.$verify(item.class,'class') +' '+ eventName +'" '+ _that.$verify(that.$reader_style(item.style),'style') +'>'+ item.title +'</a>';
                            that.event_list[eventName] = {'click':{type:'link_event',event:item.event}}
                        break;
                        case 'help':
                            var _html = '';
                            $.each(item.list,function(index,items){
                                _html += '<li>'+items +'</li>';
                            })
                            html += '<ul class="help-info-text c7'+ _that.$verify(item.class) +'"'+ _that.$verify(that.$reader_style(item.style),'style') +'>'+ _html +'</ul>';
                        break;
                    }
                    that.form_config[item.name] = item;
                });
                $.extend(that.event_list,event_list);
                return html;
            },
            
            /**
             * @description 创建事件配置
             * @param {object} item 行内配置
             * @return {object} 配置信息
            */
            $create_event_config:function(item){
                var config = {};
                if(typeof item['name'] === "undefined") return {};
                $.each(this.event_type,function(key,items){
                    if(item[items]){
                        config[(items === 'event'?'click':items)] = {type:item.type,event:item[items],cust:(['select','checkbox','radio'].indexOf(item.type) > -1?true:false),config:item};
                    }
                });
                return config;
            },
            /**
             * @description 渲染样式
             * @param {object|string} data 样式配置 
             * @return {string} 样式
            */
            $reader_style:function(data){
                var style = '';
                if(typeof data === 'string') return data;
                if(typeof data === 'undefined') return '';
                $.each(data,function(key,item){
                    style += key+':'+item+';';
                });
                return style;
            },

            /**
             * @description 渲染下拉，内容方法
            */
            $reader_select:function(item,style,attribute,index){
                var that = this,list = '',option ='',active = {};
                if(!Array.isArray(item.list)){
                    var config = item.list;
                    bt_tools.send({
                        url:config.url,
                        data:config.param || {}
                    },function(res){
                        if(res.status !== false){
                            item.list = item.list.dataFilter?item.list.dataFilter(res):res;
                            that.$replace_render_content(index);
                        }else{
                            bt.msg(res);
                        }
                    });
                }
                $.each(item.list,function(key,items){
                    if(items.value === item.value || items.value === that.config.data[item.name]){
                        active = items;
                    }else{
                        active = item.list[0];
                    }
                    list += '<li class="item'+ _that.$verify(items.value === active.value?'active':'') +' '+ (items.disabled?'disabled':'') +'">'+ items.title +'</li>';
                    option += '<option value="'+ items.value +'"'+ (items.disabled?'disabled':'') +' '+ _that.$verify(items.value === active.value?'selectd':'') +'>'+ items.title +'</option>';
                });
                if(!active.title && Array.isArray(item.list)) active = item.list[0];
                return '<div class="bt_select_updown mr10 '+ (item.disabled?'bt_disabled':'') + ' '+ _that.$verify(item.hide,'hide',true) + _that.$verify(item.class) +'" '+_that.$verify(style,'style')+' data-name="'+ item.name +'">'+
                    '<span class="bt_select_value"><span class="bt_select_content">'+ (active.title || 'Getting data') +'</span><span class="glyphicon glyphicon-triangle-bottom ml5"></span></span>'+
                    '<ul class="bt_select_list">'+ (list || '') +'</ul>'+
                    '<select'+ attribute +' class="hide" '+ (item.disabled?'disabled':'') +'>'+ (option || '') +'</select>'+
                '</div>';
            },

            /**
             * @description 替换渲染内容
            */
            $replace_render_content:function(index){
                var that = this,config = this.config.form[index];
                $('[data-form='+ that.random +']').find('.line:eq('+ index +')').replaceWith(that.$reader_content_row(index,config));
            },

            /**
             * @description 事件绑定功能
             * @param {Array} eventList 事件列表
             * @param {Function} callback 回调函数
             * @return void
            */
            $event_bind:function(eventList,callback){
                var that = this,_event = {};
                that.element = $(typeof eventList === 'object'?that.element:('[data-form='+ that.random +']'));
                if(typeof eventList === 'undefined') _event = that.event_list;
                $.each(_event,function(key,item){
                    if($.isEmptyObject(item)) return true;
                    $.each(item,function(keys,items){
                        var childNode = '';
                        if(typeof items.cust === "boolean"){
                            childNode = '['+(items.cust?'data-':'')+'name='+ key +']';
                        }else{
                            childNode = '.'+ key;
                        }
                        (function(items,key){
                            if(items.onEvent === false){
                                switch(items.type){
                                    case 'input_checked':
                                        $(childNode).on(keys != 'event'?keys:'click',function(ev){
                                            items.event.apply(this,[ev,that]);
                                        });
                                    break;
                                }
                                return true;
                            }else{
                                that.element.on(keys != 'event'?keys:'click',items.children?items.children:childNode,function(ev){
                                    var form = that.$get_form_element(),value = that.$get_form_value(),config = that.form_config[key];
                                    switch(items.type){
                                        case 'textarea_tips':
                                            $(this).hide().prev().focus();
                                        break;
                                        case 'custom_select':
                                            if($(this).parent().hasClass('bt-disabled')) return false;
                                            var select_value = $(this).next();
                                            if(!select_value.hasClass('show')){
                                                $('.bt_select_list').removeClass('show');
                                                select_value.addClass('show');
                                            }else{
                                                select_value.removeClass('show');
                                            }
                                            $(document).click(function(){
                                                that.element.find('.bt_select_list').removeClass('show');
                                                $(this).unbind('click');
                                                return false;
                                            });
                                            return false;
                                        break;
                                        case 'custom_select_item':
                                            config = that.form_config[$(this).parents('.bt_select_updown').attr('data-name')],item_config = config.list[$(this).index()]
                                            if($(this).hasClass('disabled')){
                                                $(this).parent().removeClass('show');
                                                if(item_config.tips) layer.msg(item_config.tips,{icon:2});
                                                return true;
                                            }
                                            if(!$(this).hasClass('active') && !$(this).hasClass('disabled')){
                                                $(this).parent().prev().find('.bt_select_content').text($(this).text());
                                                $(this).addClass('active').siblings().removeClass('active');
                                                $(this).parent().next().val(item_config.value.toString());
                                                $(this).parent().removeClass('show');
                                                $(this).parent().next().trigger("change");
                                            }
                                        break;
                                        case 'select_path':
                                            bt.select_path('event_'+$(this).prev().attr('name')+'_'+that.random);
                                        break; 
                                    }
                                    if(items.event) items.event.apply(this,[value,form,that,config,ev]); // 事件
                                    if(items.added) items.added.apply(this,[ev,config]);
                                });
                            }
                        }(items,key));
                    });
                });
                if(callback) callback();
            },

            /**
             * @description 获取表单数据
             * @return {object} 表单数据
             */
            $get_form_value:function(){
                return this.element.serializeObject();
            },

            /**
             * @description 设置指定数据
             * 
            */
            $set_find_value:function(name,value){
                var config = {},that = this;
                typeof name != 'string'?config = name:config[name] = value;
                $.each(config,function(key,item){
                    that.form_element[key].val(item);
                });
            },

            /**
             * @description 获取Form，jquery节点
             * @param {Boolean} afresh 是否强制刷新
             * @return {object} 
             */
            $get_form_element:function(afresh){
                var form = {},that = this;
                if(afresh || $.isEmptyObject(that.form_element)){
                    this.element.find(':input').each(function(index){
                        form[$(this).attr('name')] = $(this);
                    });
                    that.form_element = form;
                }else{
                    return that.form_element;
                }
            },

            /**
             * @description 验证值整个列表是否存在，存在则转换成属性字符串格式
             */
            $verify_group:function(config,group){
                var that = this,str = '';
                $.each(group,function(index,item){
                    if(typeof config[item] === "undefined") return true;
                    if(['disabled','readonly'].indexOf(item) > -1){
                        str += ' ' + (config[item]?(item+'="'+item +'"'):'');
                    }else{
                        str += ' '+ item + '="' + config[item] +'"';
                    }
                });
                return str;
            },

            /**
             * @description 验证绑定事件
             * @param {String} value 
             */
            $verify_bind_event:function(eventName,row,group){
                var event_list = {};
                $.each(group,function(index,items){
                    var event_fun = row[items];
                    if(event_fun){
                        if(typeof event_list[eventName] === "object"){
                            if(!Array.isArray(event_list[eventName])) event_list[eventName] = [event_list[eventName]];
                            event_list[eventName].push({event:event_fun,eventType:items});
                        }else{
                            event_list[eventName] = {event:event_fun,eventType:items};
                        }
                    }
                });
                return event_list;
            },

            /**
             * @description 验证值是否存在
             * @param {String} value 内容/值
             * @param {String|Boolean} attr 属性
             * @param {String} type 属性
            */
            $verify:function(value,attr,type){
                if(!value) return '';
                if(type === true) return value?' '+ attr:'';
                if(type === 'style') return attr?attr+':'+value+';':value;
                return attr?' '+ attr+'="'+value+'"':' '+value;
            },
            
            /**
             * @description 提交内容，需要传入url
             * @param {Object|Function} param 附加参数或回调函数
             * @param {Function} callback 回调
             */
            $submit:function(param,callback){

            }
        }
        return new ReaderForm(config);
    },
    /**
     * @description tab切换，支持三种模式
     * @param {object} config
     * @return 当前实例对象
    */
    tab:function(config){
        var _that = this;
        function ReaderTab(config){
            this.config = config;
            this.theme = this.config.theme || {};
            this.$load();
        }
        ReaderTab.prototype = {
            type:1,
            theme_list:[
                {content:'tab-body',nav:'tab-nav',body:'tab-con',active:'on'},
                {content:'bt-w-body',nav:'bt-w-menu',body:'bt-w-con'}
            ],
            random:bt.get_random(5),
            $init:function(){
                var that = this,active = this.config.active,config = that.config.list,_theme = {};
                this.$event_bind();
                if(config[that.active].success) config[that.active].success();
                config[that.active]['init'] = true;
            },
            $load:function(){
                var that = this;

            },
            $reader_content:function(){
                var that = this,_list = that.config.list,_tab = '',_tab_con = '',_theme = that.theme,config = that.config;
                if(typeof that.active === "undefined") that.active = 0;
                if(!$.isEmptyObject(config.theme)){
                    _theme = this.theme_list[that.active];
                    $.each(config.theme,function(key,item){
                        if(_theme[key]) _theme[key] += ' ' + item;
                    });
                    that.theme = _theme;
                }
                if(config.type && $.isEmptyObject(config.theme)) this.theme = this.theme_list[that.active];
                $.each(_list,function(index,item){
                    var active = (that.active === index?true:false),_active = _theme['active'] || 'active';
                    _tab += '<span class="'+ (active?_active:'') +'">'+ item.title +'</span>';
                    _tab_con += '<div class="tab-block '+ (active?_active:'') +'">'+ (active?item.content:'') +'</div>';
                });
                that.element = $('<div id="tab_'+ that.random +'" class="'+ _theme['content'] + _that.$verify(that.config.class) +'"><div class="'+ _theme['nav'] +'" >'+ _tab +'</div><div class="'+ _theme['body'] +'">'+ _tab_con +'</div></div>');
                return that.element[0].outerHTML;
            },
            /**
             * @description 渲染指定tab内容
            */
            $reader_find:function(){
                
            },
            /**
             * @description 事件绑定
             */
            $event_bind:function(){
                var that = this,_theme = that.theme,active = _theme['active'] || 'active';
                if(!that.el) that.element = $('#tab_'+ that.random);
                that.element.on('click',('.'+_theme['nav'].replace(/\s+/g,'.')+' span'),function(){
                    var index = $(this).index(),config = that.config.list[index];
                    $(this).addClass(active).siblings().removeClass(active);
                    $('.'+_theme['body']+'>div:eq('+ index +')').addClass(active).siblings().removeClass(active);
                    that.active = index;
                    if(!config.init){
                        $('.'+_theme['body']+'>div:eq('+ index +')').html(config.content);
                        if(config.success) config.success();
                        config.init = true;
                    }
                });
            }
        }
        return new ReaderTab(config);
    },
    /**
     * @description loading过渡
     * @param {*} title 
     * @param {*} is_icon 
     * @return void
     */
    load:function(title){
        var loadT = layer.msg(title +',please wait...',{icon:16,time:0,shade:.3});
        if(title === true) loadT = layer.load();
        return {
            close:function(){
                layer.close(loadT);
            }
        }
    },
    /**
     * @description 弹窗方法，有默认的参数和重构的参数
     * @param {object} config  和layer参数一致
     * @require 当前关闭弹窗方法
    */
    open:function(config){
        var _config={},layerT = null;
        _config = $.extend({
            type:1,
            area:'640px',
            closeBtn:2,
            btn:['确认','取消'],
        },config);
        layerT = layer.open(_config);
        return {
            close:function(){
                layer.close(layerT);
            }
        }
    },
    /**
     * @description 封装msg方法
     * @param {object|string} param1 配置参数,请求方法参数
     * @param {number} param2 图标ID
     *  @require 当前关闭弹窗方法
    */
    msg:function(param1,param2){
        var layerT = null,msg = '',config = {};
        if(typeof param1 === "object"){
            if(typeof param1.status === "boolean"){
                msg = param1.msg,config = {icon:param1.status?1:2};
            }
        }
        if(typeof param1 === "string"){
            msg = param1,config = {icon:typeof param2 !== 'undefined'?param2:1}
        }
        layerT = layer.msg(msg,config);
        return {
            close:function(){
                layer.close(layerT);
            }
        }
    },
    /**
     * @description 验证值是否存在
     * @param {String} value 内容/值
     * @param {String|Boolean} attr 属性
     * @param {String} type 属性
    */
    $verify:function(value,attr,type){
        if(!value) return '';
        if(type === true) return value?' '+ attr:'';
        if(type === 'style') return attr?attr+':'+value+';':value;
        return attr?' '+ attr+'="'+value+'"':' '+value;
    },
    
    /**
     * @description 选择目录
     * @param {*} datas 
     * @param {*} callback 
     * @param {*} type 
     * @param {*} limit 
     */
    select_path:function(datas,callback,type,limit){
        //if(typeof data === 'string') data = {path:data};
        //if(typeof data === 'function') type = callback,callback = data,data = {path:bt.get_cookie('Path')};
		if(typeof type !== 'number') type = 1;
		if(typeof limit !== 'number') limit = false;
		bt.set_cookie('Path','/www/server/panel/BTPanel/static');     
		var that = this,
		select_file = {
            type:type,
			type_tips:type == 0?'目录':(type == 1?'文件':'目录或文件'),
			type_limit:type == 0?'dir':(type == 1?'file':'all'),
            select_list:[],
            select_path:bt.get_cookie('Path') || (bt.os == 'Windows'?setup_path:'/www/wwwroot'),
            select_config:{},
			scroll_width:0,
			file_path: bt.get_cookie('Path'),
			file_operating:[], 
			area : [window.innerWidth, window.innerHeight],
            reader_view:function(){
                var _this = this;
                this.scroll_width = select_file.getScrollbarWidth();
                layer.open({
                    type:1,
                    title: datas.title || ('选择' + _this.type_tips),
                    shadeClose:false,
                    closeBtn: 2,
                    area:['650px','555px'],
                    content:'<div id="select_file_style"></div>\
                        <div id="select_file_directory" class="select_file_content">\
                            <div class="file_path_views">\
                                <div class="forward_path">\
                                    <span title="后退"><i class="iconfont icon-arrow-lift"></i></span>\
                                    <span title="前进" class="active"><i class="iconfont icon-arrow-right"></i></span>\
                                    <span class="file_return_level" title="上一层"><i class="iconfont icon-prev"></i></span>\
                                </div>\
                                <div class="file_path_input">\
                                    <div class="file_path_shadow"></div>\
                                    <div class="file_dir_view" data-width="244"></div>\
                                    <input type="text" data-path="C:/BtSoft/backup" class="path_input">\
                                </div>\
                                <div class="file_path_refresh" title="刷新列表"><i class="iconfont icon-shuaxin"></i></div>\
                                <div class="search_path_views">\
                                    <input type="text" placeholder="搜索文件名" class="file_search_input">\
                                    <div class="search_dir_all" style="display: none;">\
                                        <input type="checkbox" style="display:none;"/>\
                                        <span class="file_check" data-type="all" data-checkbox="0"></span>\
                                        <span>包含子目录</span>\
                                    </div>\
                                    <button type="submit" class="path_btn"><i class="iconfont icon-search"></i></button>\
                                </div>\
                            </div>\
                            <div class="select_file_tootls"><button type="button" class="creat_dir">新建文件夹</button></div>\
                            <div class="select_file_body">\
                                <div class="select_mount_list not-select" id="select_mount_list"></div>\
                                <div class="select_dir_list not-select">\
                                    <div class="select_list_thaed">\
                                        <table class="mask_thead">\
                                            <thead><tr><th data-type="filename"><span>名称</span><i class="iconfont icon-xiala"></i><i class="icon-drag"></i></th><th data-type="mtime"><span>修改时间</span><i class="iconfont icon-xiala"></i><i class="icon-drag"></i></th><th data-type="type" class="active"><span>类型</span><i class="iconfont icon-xiala"></i><i class="icon-drag"></i></th></tr></thead>\
                                        </table>\
                                        <div class="select_list_shadow"></div>\
                                    </div>\
                                    <div class="select_list_body">\
                                        <table>\
                                            <thead><tr><th><span>文件</span><i></i></th><th><span>修改时间</span><i></i></th><th><span>类型</span><i></i></th></tr></thead>\
                                            <tbody id="select_dir_list"></tbody>\
                                        </table>\
                                    </div>\
                                </div>\
                            </div>\
                            <div class="select_file_group">\
                                <div class="select-line">\
                                    <span class="select-line-name">'+ _this.type_tips +'名:</span>\
                                    <div class="select-line-content">\
                                        <input type="text" name="select_name" class="file_directory" />\
                                    </div>\
                                </div>\
                                <div class="select_btn_group">\
                                    <button class="btn btn-success btn-sm" type="button">选择'+  (_this.type_tips == '目录或文件'?'':_this.type_tips) +'</button>\
                                    <button class="btn btn-default btn-sm" type="button">取消</button>\
                                </div>\
                            </div>\
                        </div>',
                    success:function(){
                        //_this.event_bind();
                        _this.render_file_list();
                        $('.select_list_thaed').css('right',_this.scroll_width+'px');
                    }
                });
            },
            /**
             * @description 渲染文件列表
             * @param {object} data 配置参数，包含path路径、serarch搜索字段
            */
            render_file_list:function(data,callback){
                var mount_html = '',dir_html = '',_this = this,datas = {path:this.select_path,sort:'type',disk:true};
                if(typeof data == "undefined") data = datas;
                if(typeof data == "function") callback = data,data = datas;
				_this.select_config = $.extend(datas,data);
                that.$http('GetDir',_this.select_config,function(rdata){
                    var disk_list = rdata.DISK,dir_list = $.merge(_this.data_reconstruction(rdata.DIR,'DIR') ,_this.data_reconstruction(rdata.FILES));
                    _this.select_list = dir_list;
					_this.render_path_list();
                    $.each(disk_list,function(index,item){
                        var name = (item.path == '/'?'根目录':item.path.indexOf(':/') > -1?('本地磁盘('+ item.path.match(/[A-Z]+/)[0])+ ':)':item.path)
                        mount_html += '<div class="item" data-menu="'+ item.path +'" title="名称:&nbsp;'+ name +'\n路径:&nbsp;'+ item.path +'\n总容量:&nbsp;'+ item.size[0] +'\n可用容量:&nbsp;'+ item.size[2] +'">'+
                            '<span class="glyphicon glyphicon-hdd mr5"></span>'+
                            '<span>'+ name +'</span>'+
                        '</div>';
					});
					
                    $.each(dir_list,function(index,item){
						if((_this.type == 0) && item.type != _this.type_limit) return true;
						var mtime = bt.format_data(item.mtime),
						type = (item.type == 'dir'?'文件夹':'文件');
						dir_html += '<tr data-index="'+ index +'" title="名称：'+ item.filename +'\r修改时间:'+ mtime +'\r类型：'+ type +'" data-path="'+ item.filename +'" data-type="'+ item.type +'">\
                            <td><span><i class="'+ item.type +'-icon"></i><span>'+ item.filename +'</span></span></td>\
                            <td><span>'+ mtime +'</span></td>\
                            <td><span>'+ (item.type == 'dir'?'文件夹':'文件') +'</span></td>\
                        </tr>';
                    });
                    $('#select_mount_list').html(mount_html);
					$('#select_dir_list').html(dir_html);
                    if(callback) callback(rdata);
                });
            },
            /**
             * @description 渲染路径列表
             * @param {Function} callback 回调函数
             * @return void
            */
            
			data_reconstruction:function(data,type,callback){
				if(data.length < 1) return [];
				var _array = [];
				$.each(data,function(index,item){
					var itemD = item.split(";"),fileMsg ='',fileN = itemD[0].split('.'),extName = fileN[fileN.length - 1];
					switch(itemD[0]) {
						case '.user.ini':
							fileMsg = 'PS: PHP用户配置文件(防跨站)!';
							break;
						case '.htaccess':
							fileMsg = 'PS: Apache用户配置文件(伪静态)';
							break;
						case 'swap':
							fileMsg = 'PS: 宝塔默认设置的SWAP交换分区文件';
							break;
					}
					if(itemD[0].indexOf('Recycle_bin') != -1) fileMsg = 'PS: 回收站目录,勿动!';
					if(itemD[0].indexOf('.upload.tmp') != -1) fileMsg = 'PS: 宝塔文件上传临时文件,重新上传从断点续传,可删除';
					_array.push({
						caret: itemD[8] == '1'?true:false,             //是否收藏
						down_id: itemD[9],                            //是否分享 分享id
						ext: (type == 'DIR'?'':extName),               //文件类型
						filename: itemD[0],                            //文件名称
						mtime: itemD[2],                               //时间
						ps: fileMsg || itemD[10],                      //备注
						size: itemD[1],                                //文件大小
						type: type == 'DIR'?'dir':'file',              //文件类型
						user: itemD[3],                                //用户权限
						root_level:itemD[4]                            //所有者
						// accept: 666,
						//composer: 0,                       
						// link: "",
						// shell: false,
					})
		
				})
				return _array;
			},
			render_path_list: function (callback){
				var _this = this,html = '<div class="file_dir_omit hide" title="展开已隐藏的目录"><span></span><i class="iconfont icon-zhixiang-zuo"></i><div class="nav_down_list"></div></div>', path_before = '',dir_list = this.file_path.split("/").splice(1),first_dir = this.file_path.split("/")[0];
				if(bt.os === 'Windows'){
					if(dir_list.length == 0) dir_list = [];
					dir_list.unshift('<span class="glyphicon glyphicon-hdd"></span><span class="ml5">本地磁盘('+ first_dir +')</span>');
				}else{
					if(this.file_path == '/') dir_list = [];
					dir_list.unshift('根目录');
				}
				for(var i = 0; i < dir_list.length; i++){
					path_before += '/' + dir_list[i];
					if (i == 0) path_before = '';
					html += '<div class="file_dir_item">\
								<span class="file_dir" title="' + (first_dir + path_before) + '">' + dir_list[i] + '</span>\
								<i class="iconfont icon-arrow-right"></i>\
								<ul class="nav_down_list">\
									<li data-path="*"><span>加载中</span></li>\
								</ul>\
							</div>';
				}
				$('.path_input').val('').attr('data-path',this.file_path);
				var file_dir_view = $('.file_path_input .file_dir_view');
				file_dir_view.html(html);
				file_dir_view.attr('data-width',file_dir_view.width());
				_this.set_dir_view_resize();
			},

            /**
             * @description 设置标题宽度
             * @param {string} th_index 表头序列号
             * @param {string} style class样式
            */
            set_select_width:function(th_index,style){
                var _this = this,className = '.select_dir_list tbody td:nth-child('+ (th_index+1) +')>span,.select_dir_list thead th:nth-child('+ (th_index+1) +')>span',style_index = $('#th-index-'+th_index);
                if(style_index.length > 0){
                    style_index.html(className +'{'+ style +'}');
                }else{
                    $('#select_file_style').append('<style type="text/css" id="th-index-'+ th_index +'">'+ className +'{'+ style +'}' +'</style>');
                }
            },
            /**
             * @description 样式转换文件样式
             * @param {string} style 样式
             */
            cut_style_object:function(style){
                var object = {},arry = style.split(';');
                console.log(arry);
                return object;
            },
            /**
             * @description 获取滚动条宽度
             */
            getScrollbarWidth:function(){
                var odiv = document.createElement('div'),//创建一个div
                    styles = {
                        width: '100px',
                        height: '100px',
                        overflowY: 'scroll'//让他有滚动条
                    }, i, scrollbarWidth;
                for (i in styles) odiv.style[i] = styles[i];
                document.body.appendChild(odiv);//把div添加到body中
                scrollbarWidth = odiv.offsetWidth - odiv.clientWidth;//相减
                odiv.remove();//移除创建的div
                return scrollbarWidth;//返回滚动条宽度
			},
			set_dir_view_resize:function(){
				var file_path_input = $('.file_path_input'),file_dir_view = $('.file_path_input .file_dir_view'),_path_width = file_dir_view.attr('data-width'),file_item_hide = null;
				if(_path_width){
					parseInt(_path_width);
				}else{
					_path_width = file_dir_view.width();
					file_dir_view.attr('data-width',_path_width);
				}
				if(file_dir_view.width() - _path_width < 90){
					var width = 0;
					$($('.file_path_input .file_dir_view .file_dir_item').toArray().reverse()).each(function(){
						var item_width = 0;
						if(!$(this).attr('data-width')){
							$(this).attr('data-width',$(this).width());
							item_width = $(this).width();
						}else{
							item_width = parseInt($(this).attr('data-width'));
						}
						width += item_width;
						if((file_path_input.width() - width) <= 90){
							$(this).addClass('hide');
						}else{
							$(this).removeClass('hide');
						}
					});
				}
				var file_item_hide = file_dir_view.children('.file_dir_item.hide').clone(true);
				if(file_dir_view.children('.file_dir_item.hide').length == 0){
					file_path_input.removeClass('active').find('.file_dir_omit').addClass('hide');
				}else{
					file_item_hide.each(function(){
						if($(this).find('.glyphicon-hdd').length == 0){
							$(this).find('.file_dir').before('<span class="file_dir_icon"></span>');
						}
					});
					file_path_input.addClass('active').find('.file_dir_omit').removeClass('hide');
					file_path_input.find('.file_dir_omit .nav_down_list').empty().append(file_item_hide);
					file_path_input.find('.file_dir_omit .nav_down_list .file_dir_item').removeClass('hide');
				}
			},
			/**
			 * @description 渲染文件列表
			 * @param {Object} data 参数对象，例如分页、显示数量、排序，不传参数使用默认或继承参数
			 * @param {Function} callback 回调函数
			 * @return void
			*/
			reader_file_list:function (data, callback){
				var _this = this,select_page_num = '',next_path = '';
				if(typeof data === "function") callback = data,data = {is_operating:false};
				if(typeof data === "undefined") data = {is_operating:false};
				if(limit){
					layer.msg('只能在该目录下操作',{icon:2});
					return false;
				}
				this.loadT = bt.load('正在获取文件列表,请稍候...');
				this.file_images_list = [];
				_this.get_dir_list(data,function(res){
					_this.loadT.close();
					_this.file_list = $.merge(_this.data_reconstruction(res.DIR,'DIR'), _this.data_reconstruction(res.FILES));
					_this.file_path = res.PATH;
					_this.is_recycle = res.FILE_RECYCLE;
					_this.file_store_list = res.STORE;
					bt.set_cookie('Path',res.PATH);
					
					
					var mount_html = '',dir_html = '',
					disk_list = res.DISK,
					dir_list = _this.file_list;
					_this.select_list = _this.file_list;
					_this.render_path_list();
                    $.each(disk_list,function(index,item){
                        var name = (item.path == '/'?'根目录':item.path.indexOf(':/') > -1?('本地磁盘('+ item.path.match(/[A-Z]+/)[0])+ ':)':item.path)
                        mount_html += '<div class="item" data-menu="'+ item.path +'" title="名称:&nbsp;'+ name +'\n路径:&nbsp;'+ item.path +'\n总容量:&nbsp;'+ item.size[0] +'\n可用容量:&nbsp;'+ item.size[2] +'">'+
                            '<span class="glyphicon glyphicon-hdd mr5"></span>'+
                            '<span>'+ name +'</span>'+
                        '</div>';
					});
					
                    $.each(dir_list,function(index,item){
						if((_this.type == 0) && item.type != _this.type_limit) return true;
						var mtime = bt.format_data(item.mtime),
						type = (item.type == 'dir'?'文件夹':'文件');
                        dir_html += '<tr data-index="'+ index +'" title="名称：'+ item.filename +'\r修改时间:'+ mtime +'\r类型：'+ type +'" data-path="'+ item.filename +'" data-type="'+ item.type +'">\
                            <td><span><i class="'+ item.type +'-icon"></i><span>'+ item.filename +'</span></span></td>\
                            <td><span>'+ mtime +'</span></td>\
                            <td><span>'+ (item.type == 'dir'?'文件夹':'文件') +'</span></td>\
                        </tr>';
                    });
                    $('#select_mount_list').html(mount_html);
					$('#select_dir_list').html(dir_html);
					var _i = res.PATH.lastIndexOf("\/"),
					index_file  = res.PATH.substring(_i + 1, res.PATH.length);
					//if(_this.type_limit != 'file') $('[name="select_name"].file_directory').val(index_file);
                    if(callback) callback(rdata);
				});
			},


			/**
			 * @description 渲染文件列表内容
			 * @param {Object} data 文件列表数据
			 * @param {Function} callback 回调函数
			 * @return void
			*/
			reader_file_list_content:function(data,callback){
				var _html = '',_this = this,is_dir_num = 0;
				$.each(data,function(index,item){
					var _title = item.filename + item.ps;
					_this.file_list[index] = item = _this.$file_data_dispose(item);
					_this.file_list[index]['only_index'] = index;
					if(item.filename.indexOf('Recycle_bin')) _tips = 'PS: 回收站目录,勿动!';
					if(_title.length > 20) _title = _title.substring(0, 20) + '...';
					if(bt.check_chinese(_title) && _title.length > 10) _title = _title.substring(0, 10) + '...'
					_html += '<div class="file_tr" data-index="'+ index +'">'+
						'<div class="file_td file_checkbox"><div class="file_check"></div></div>'+
						'<div class="file_td file_name">'+
							'<div class="file_ico_type"><i class="file_icon '+ (item.type == 'dir'?'file_folder':(item.ext == ''?'':'file_'+item.ext)) +'"></i></div>'+
							'<span class="file_title file_'+ item.type +'_status" title="' + _this.file_path +'/'+ item.filename + '"><i>'+ item.filename + item.ps +'</i></span>'+ (item.caret?'<span class="iconfont icon-favorites" style="'+ (item.down_id?'right:30px':'') +'" title="文件已收藏，点击取消"></span>':'') + (item.down_id?'<span class="iconfont icon-share1" title="文件已分享，点击查看信息"></span>':'') +
						'</div>'+
						'<div class="file_td file_type"><span title="'+ item.type_tips +'">'+  item.type_tips +'</span></div>'+
						'<div class="file_td file_size"><span>'+ (item.type == 'dir'?'<a class="btlink folder_size" href="javascript:;" data-path="'+ (_this.file_path+'/'+item.filename) +'">点击计算</a>':bt.format_size(item.size)) +'</span></div>'+
						'<div class="file_td file_mtime"><span>' + bt.format_data(item.mtime) + '</span></div>'+
					'</div>';
					if(item.type == 'dir') is_dir_num ++; // 获取目录数量
					if(item.ispreview){ // 获取图片数量
						_this.file_images_list.push(item.path);
						if(typeof item.images_id) item.images_id = _this.file_images_list.length - 1;
					}

				});
				$('.file_list_content').html(_html);
				if(callback) callback({is_dir_num:is_dir_num})
			},
			/**
			 * @description 文件数据处理
			 * @param {Object} data 配置参数
			 * @return {Object} 重新生成的文件对象
			 */
			$file_data_dispose:function(data){
				var models = {languages:null,model:null};
				//if(data.type !== 'dir') models = this.$get_file_model(data);
				return $.extend(data,{
					only_id:bt.get_random(10), // 文件唯一ID
					type_tips:data.type === 'dir'?'文件夹':this.ext_type_tips(data.ext), // 文件类型描述
					open_type:this.determine_file_type(data.ext), // 打开类型
					languages:models.languages, // 文件语言
					path:data.path || this.path_resolve(this.file_path,data.filename), // 文件全路径
					model:models.model, // 语言模型
				});
			},
			/**
				 * @description 文件路径合并
				 * @param {String} paths 旧路径
				 * @param {String} param 新路径
				 * @return {String} 新的路径
			*/
			path_resolve:function(paths, param){
				var path = '',split = '';
				if(!Array.isArray(param)) param = [param];
				paths.replace(/([\/|\/]*)$/,function($1){
					split = $1;
					return 'www';
				});
				$.each(param,function(index,item){
					path += '/' + item;
				});
				return paths + path;
			},
			/**
				 * @description 获取文件语言配置模型
				 * @param {Object} data 当前文件的数据对象
				 * @return {Object} 当前语言配置模型
			*/
			$get_file_model:function(data){
				var config = this.vscode_editor.config;
				for(languages in config.supportedModes){
					var item = config.supportedModes[languages];
					for(var j=0;j<item[0].length;j++){
						console.log(data.ext,item[0][j]);
						if(data.ext === item[0][j]) return {languages:languages,model:item[1]};
					}
				}
				return {languages:'text',model:'Text'};
			},
			/**
			 * @description 渲染文件磁盘列表
			 * @return void
			*/
			render_file_disk_list:function(){
				var _this = this,html = '';
				_this.get_disk_list(function(res){
					$.each(res,function(index,item){
						html += '<div class="nav_btn" data-menu="'+ item.path +'">'+
							'<span class="glyphicon glyphicon-hdd"></span>'+
							'<span>'+(item.path == '/'?'根目录':item.path)+' ('+ item.size[2] +')</span>'+
						'</div>';
					});
					$('.mount_disk_list').html(html);
				});
			},
			/**
				 * @description 文件类型判断，或返回格式类型(不传入type)
				 * @param {String} ext
				 * @param {String} type
				 * @return {Boolean|Object} 返回类型或类型是否支持
			*/
			determine_file_type:function(ext,type){
				var config = {
					images:['jpg','jpeg','png','bmp','gif','tiff','ico'],
					compress:['zip','rar','gz','war','tgz'],
					video:['mp4', 'mpeg', 'mpg', 'mov', 'avi', 'webm', 'mkv'],
					ont_text:['iso','xlsx','xsl','doc','docx','tiff','exe','so','7z','bz','dmg','apk']
				},returnVal = false;
				if(type != undefined){
					if(type == 'text'){
						$.each(config,function(key,item){
							$.each(item,function(index,items){
								if(items == ext){
									returnVal = true;
									return false;
								}
							})
						});
						returnVal = !returnVal
					}else{
						if(typeof config[type] == "undefined") return false;
						$.each(config[type],function(key,item){
							if(item == ext){
								returnVal = true;
								return false;
							}
						});
					}
				}else{
					$.each(config,function(key,item){
						$.each(item,function(index,items){
							if(items == ext){
								returnVal = key;
								return false;
							}
						})
					});
					if(typeof returnVal == "boolean") returnVal = 'text';
				}
				return returnVal;
			},

			/**
			 * @description 渲染右键鼠标菜单
			 * @param {Object} ev 事件event对象
			 * @param {Object} el 事件对象DOM
			 * @return void
			*/
			render_file_groud_menu: function (ev,el){
				var _this = this,index = $(el).data('index'),data = _this.file_list[index],config_group = [['open','打开'],['split',''],['download','下载'],['share','分享目录/文件'],['cancel_share','取消分享'],['favorites','收藏目录/文件'],['cancel_favorites','取消收藏'],['split',''],['dir_kill','目录查杀'],['authority','权限'],['split',''],['copy','复制'],['shear','剪切'],['rename','重命名'],['del','删除'],['split',''],['killing','创建压缩',[['gzip','tar.gz (推荐)'],['zip','zip (通用格式)'],['rar','rar (中文兼容较好)']]],['unzip','解压',[['local','解压到当前'],['folad','解压到当前']]]],compression = ['zip','rar','gz','war','tgz','bz2'],offsetNum = 0;
				if(data.type == 'dir'){ // 判断是否为目录，目录不可下载
					config_group.splice(2,1);
					offsetNum ++;
				}
				if(data.down_id !== 0){ //判断是否分享
					config_group.splice(3-offsetNum,1);
					offsetNum ++;
				}else{
					config_group.splice(4-offsetNum,1);
					config_group[3-offsetNum][1] = (data.type == 'dir'?'分享目录':'分享文件');
					offsetNum ++;
				}
				if(data.caret !== false){ // 判断是否收藏
					config_group.splice((5-offsetNum),1);
					offsetNum ++;
				}else{
					config_group.splice((6-offsetNum),1);
					config_group[5-offsetNum][1] = (data.type == 'dir'?'收藏目录':'收藏文件');
					offsetNum ++;
				}
				if(data.ext != 'php' && data.type != 'dir'){ // 判断是否为php，非php文件（排除目录）无法扫描
					config_group.splice((8-offsetNum),1);
					offsetNum ++;
				}
				var num = 0;
				$.each(compression,function(index,item){
					if(item == data.ext) num ++;
				});
				if(num == 0){
					config_group.splice((17-offsetNum),1);
					offsetNum ++;
				}
				_this.reader_menu_list({el:$('.selection_right_menu'),ev:ev,data:data,list:config_group});
			},

			/**
			 * @description 渲染右键全局菜单
			 * @param {Object} ev 事件event对象
			 * @param {Object} el 事件对象DOM
			 * @return void
			*/
			render_file_all_menu:function (ev,el) {
				var _this = this,config_group = [['refresh','刷新'],['split',''],['upload','上传'],['create','新建文件夹/文件',[['create_dir','新建文件夹'],['create_files','新建文件']]],['split',''],['paste','粘贴']],offsetNum = 0;
				if(!bt.get_storage('session','copy_path')){
					config_group.splice(5,1);
					offsetNum ++;
				}
				_this.reader_menu_list({el:$('.selection_right_menu'),ev:ev,data:{},list:config_group});
			},
			get_dir_list:function(data, callback,is_tips) {
				var _this = this;
				if(typeof callback === "boolean") is_tips = callback,callback = null;
				that.$http('GetDir',$.extend({
					disk:true,
					path:_this.file_path,
					sort:bt.get_cookie('files_sort') || 'type',
				},data),callback,is_tips);
			},
			/**
				 * @description 返回上一层目录地址
				 * @param {String} path 当前路径
				 * @returns 返回上一层地址
			*/
			retrun_prev_path:function(path){
				var dir_list = path.split('/');
				dir_list.splice(dir_list.length - 1);
				return dir_list.join('/');
			},

			/**
			* @description 渲染菜单列表
			* @param {Object} config 菜单配置列表和数据
			* @returns void
			*/
			reader_menu_list:function(config){
				var _this = this,el = config.el.find('ul'),el_height = el.height(),el_width = el.width(),left = config.ev.clientX - ((this.area[0] - config.ev.clientX) < el_width?el_width:0);
				el.empty();
				$.each(config.list,function(index,item){
					var $children = null,$children_list = null;
					if(item[0] == 'split'){
						el.append('<li class="separate"></li>');
					}else{
						if(Array.isArray(item[2])){
							$children = $('<div class="file_menu_down"><span class="glyphicon glyphicon-triangle-right" aria-hidden="true"></span><ul class="set_group"></ul></div>');
							$children_list = $children.find('.set_group');
							$.each(item[2],function(indexs,items) {
								$children_list.append($('<li><i class="file_menu_icon '+ items[0] +'_file_icon"></i><span>'+ items[1] +'</span></li>').on('click',{type:items[0],data:config.data},function(ev){
									_this.file_groud_event($.extend(ev.data.data,{
										open:ev.data.type,
										index:parseInt($(config.ev.currentTarget).data('index')),
										element:config.ev.currentTarget,
										type_tips:item.type?'文件夹':'文件'
									}));
									config.el.removeAttr('style');
									ev.stopPropagation();
									ev.preventDefault();
								}))
							});
						}
						el.append($('<li><i class="file_menu_icon '+ item[0] +'_file_icon '+ (function(type){
							switch(type){
								case 'share':
								case 'cancel_share':
									return 'iconfont icon-share';
								break;
								case 'dir_kill':
									return 'iconfont icon-dir_kill'
								break;
								case 'authority':
									return 'iconfont icon-authority';
								break;
							}
							return '';
						}(item[0])) +'"></i><span>'+ item[1] +'</span></li>').append($children).on('click',{type:item[0],data:config.data},function(ev){
							_this.file_groud_event($.extend(ev.data.data,{
								open:ev.data.type,
								index:parseInt($(config.ev.currentTarget).data('index')),
								element:config.ev.currentTarget,
								type_tips:item.type?'文件夹':'文件'
							}));
							config.el.removeAttr('style');
							ev.stopPropagation();
							ev.preventDefault();
						}));
					}
				});
				config.el.css({
					left: left,
					top: config.ev.clientY - ((this.area[1] - config.ev.clientY) < el_height?el_height:0)
				}).removeClass('left_menu right_menu').addClass(this.area[0] - (left + el_width) < 230?'left_menu':'right_menu');
				$(document).one('click',function(e){
					$(config.ev.currentTarget).removeClass('selected');
					config.el.removeAttr('style');
					e.stopPropagation();
					e.preventDefault();
				});
			},


			/**
			 * @description 返回后缀类型说明
			 * @param {String} ext 后缀类型
			 * @return {String} 文件类型
			*/
			ext_type_tips:function(ext){
				var config = {ai:"Adobe Illustrator格式图形",apk:"安卓安装包",asp:"动态网页文件",bat:"批处理文件",bin:"二进制文件",bas:"BASIC源文件",bak:"备份文件",css:'CSS样式表',cad:"备份文件",cxx:"C++源代码文件",crt:"认证文件",cpp:"C++代码文件",conf:"配置文件",dat:"数据文件",der:"认证文件",doc:"Microsoft Office Word 97-2003 文档",docx:"Microsoft Office Word 2007 文档",exe:"程序应用",gif:"图形文件",go:"Go语言源文件",htm:"超文本文档",html:"超文本文档",ico:"图形文件",java:"Java源文件",jsp:"HTML网页",jpe:"图形文件",jpeg:"图形文件",jpg:"图形文件",log:"日志文件",link:"快捷方式文件",js:"Javascript源文件",mdb:"Microsoft Access数据库",mp3:"音频文件",mp4:"视频文件",mng:"多映像网络图形",msi:"Windows Installe安装文件包",png:"图形文件",py:"Python源代码",pyc:"Python字节码文件",pdf:"文档格式文件",ppt:"Microsoft Powerpoint 97-2003 幻灯片演示文稿",pptx:"Microsoft Powerpoint2007 幻灯片演示文稿",psd:"Adobe photoshop位图文件",pl:"Perl脚本语言",rar:"RAR压缩文件",reg:"注册表文件",sys:"系统文件",sql:"数据库文件",sh:"Shell脚本文件",txt:"文本格式",vb:"Visual Basic的一种宏语言",xml:"扩展标记语言",xls:"Microsoft Office Excel 97-2003 工作表",xlsx:"Microsoft Office Excel 2007 工作表",gz:"压缩文件",zip:"ZIP压缩文件",z:"","7z":"7Z压缩文件",json:'JSON文本'};
				return typeof config[ext] != "undefined"?config[ext]:(ext+'文件');
			},
			/**
             * @description 事件绑定
            */
			event_bind: function(){
				var _this = this;
				//单击选中文件
                $('#select_dir_list').on('click','tr[data-index]',function(e){
					var index = $(this).data('index'),
					_type = $(this).attr('data-type'),
					select_name_val = (_this.type_limit=='file' && _type == 'dir')?'':_this.select_list[index].filename;
					$(this).addClass('active').siblings().removeClass('active');
					$('[name="select_name"]').val(select_name_val);
					if (_type == 'file'){
						$('.file_path_views .forward_path span:eq(1)').addClass('active');
					}else{
						$('.file_path_views .forward_path span:eq(1)').removeClass('active');
					}
                });
                $('.select_list_body').on('scroll',function(e){
                    var top = $(this).scrollTop(),left = $(this).scrollLeft();
                    if(top > 0){
                        $('.select_list_shadow').show();
                    }else{
                        $('.select_list_shadow').hide();
                    }
                    if(left >= 0){
                        $('.select_list_thaed').css('left',(4-left ) +'px');
                    }
                    e.stopPropagation();
                    e.preventDefault();
                });
				//文件刷新按钮
				$('.file_path_refresh').on('click',function(){
                    _this.render_file_list();
                });
                $('.select_dir_list thead th .icon-drag').on('mousedown',function(ev){
                    var x = ev.clientX,th = $(this).parent(),th_index = th.index(),th_width = th[0].clientWidth,min_width = parseInt($(this).parent().attr('data-min')),timeOut = null;
                    if(ev.which === 1){
                        var document_mousemove = function(e){
                            var move_x = e.clientX,offset_x = move_x - x,_width = th_width + offset_x;
                            timeOut = setTimeout(function(){
                                _this.set_select_width(th_index,'width:'+_width+'px');
                            },0);
                        },
                        document_mouseup = function(){
                            console.log(document_mouseup);
                            $(this).unbind(document_mousemove);
                            $(this).unbind(document_mouseup);
                        };
                        $(document).on('mousemove',document_mousemove).one('mouseup',function(){
                            $(this).unbind(document_mousemove);
                            $(this).unbind(this);
                        })
                    }
                    ev.stopPropagation();
                });
                $('.select_dir_list thead th>span').on('click',function(ev){
                    var th = $(this).parent(),type = th.data('type'),is_active = th.hasClass('active'),is_sort = th.hasClass('sort');
                    if(is_active){
                        th.addClass('sort').removeClass('active');
                    }else if(is_sort){
                        th.addClass('active').removeClass('sort');
                    }else{
                        th.addClass('active');
                    }
                    th.siblings().removeClass('active sort');
                    _this.render_file_list({sort:type,reverse:is_active?1:0});
                    ev.stopPropagation();
                });
                $('.search_path_views input').on('keyup',function(){
                    var val = $(this).val();
                    console.log(val);
                });
                $('.search_path_views input').focus(function(){
                    $(this).next().show();
                }).blur(function(){
                    $(this).next().hide();
                });
				//提交选中文件
				$('#select_file_directory .select_file_group').on('click','.select_btn_group .btn-success',function(e){
					var select_val = $('[name="select_name"]').val(),
					submit_val = '';
					if (select_val == '') {
						layer.msg('只能选择' + _this.type_tips,{icon:2});
					}else{
						submit_val = _this.file_path+'/'+select_val;
						console.log(submit_val)
					}
				});
				//新建文件夹
				$('#select_file_directory .select_file_tootls').on('click','.creat_dir',function(e){
					var a = "<tr><td colspan='2'><span class='glyphicon glyphicon-folder-open'></span> <input id='newFolderName' class='newFolderName' type='text' value=''></td><td colspan='3'><button id='nameOk' type='button' class='btn btn-success btn-sm'>"+lan.public.ok+"</button>&nbsp;&nbsp;<button id='nameNOk' type='button' class='btn btn-default btn-sm'>"+lan.public.cancel+"</button></td></tr>";
					if($("#tbody tr").length == 0) {
						$("#select_dir_list").append(a)
					} else {
						$("#select_dir_list tr:first-child").before(a)
					}
					$(".newFolderName").focus();
					$("#nameOk").click(function() {
						var c = $("#newFolderName").val(),
						b = $(".file_path_views .path_input").attr("data-path");
						newTxt = b+"/"+ c;
						that.$http('CreateDir', {'path': newTxt},function(e){
							if(e.status == true) {
								_this.reader_file_list({path:b,is_operating:false});
								layer.msg(e.msg, {icon: 1});
							} else {
								layer.msg(e.msg, {icon: 2});
							}
						});
					});
				});
				// 左侧根目录点击跳转
				$('#select_mount_list').on('click','.item',function(){					
					_this.reader_file_list({path:$(this).attr('data-menu'),is_operating:true});
				});

				
				// 窗口大小限制
				$(window).resize(function(ev){
					if($(this)[0].innerHeight != _this.area[1]){
						_this.area[1] = $(this)[0].innerHeight;
						_this.set_file_view();
					}
					if($(this)[0].innerWidth != _this.area[0]){
						_this.area[0] = $(this)[0].innerWidth;
						_this.set_dir_view_resize();
						// _this.set_file_table_width();
					}
					if(_this.vscode_editor.view){
						if(_this.vscode_editor.is_full_min > 0){
							layer.style(_this.vscode_editor.view,{
								'top':0,
								'left':0,'width':_this.area[0],
								'height':_this.area[1]
							});
						}
					}
					if(_this.vscode_editor.view && $.isEmptyObject(_this.vscode_editor.list)) _this.vscode.layout();
					// console.log($.isEmptyObject(_this.vscode_editor.list));
				}).keydown(function(e){ // 全局按键事件
					e = window.event || e;
					var keyCode = e.keyCode,tagName = e.target.tagName.toLowerCase();
					if(keyCode == 8 && tagName !== 'input' && tagName !== 'textarea'){ //退格键 -> 后退操作
						if(_this.vscode_editor.view == null){
							$('.forward_path span:eq(0)').click();
						}
						return false;
					}
				});
		
				// 文件路径事件（获取焦点、失去焦点、回车提交）
				$('.file_path_input .path_input').on('focus blur keyup',function(e){
					e = e || window.event;
					var path = $(this).attr('data-path');
					switch(e.type){
						case 'focus':
							$(this).addClass('focus').val(path).prev().hide();
						break;
						case 'blur':
							$(this).removeClass('focus').val('').prev().show();
						break;
						case 'keyup':
							if(e.keyCode != 13 && e.type == 'keyup') return false;
							var _val = $(this);
							if($(this).data('path') != $(this).val()){
								_this.reader_file_list({path:$(this).val(),is_operating:true},function(res){
									if(res.status === false){
										$(_val).val(path);
									}else{
										$(_val).val(res.PATH);
										$(_val).blur().prev().show();
									}
								});
							}
						break;
					}
					e.stopPropagation();
				});
		
				// 文件路径点击跳转
				$('.file_path_input .file_dir_view').on('click','.file_dir',function(){					
					_this.reader_file_list({path:$(this).attr('title'),is_operating:true});
				});
		
				// 操作前进或后退
				$('.forward_path span').click(function(){
					var index = $(this).index(),path = '';
					if(!$(this).hasClass('active')){
						switch(index){
							case 0:
								_this.file_pointer = _this.file_pointer - 1
								path = _this.retrun_prev_path(_this.file_path);
							break;
							case 1:
								_this.file_pointer = _this.file_pointer + 1
								//path = _this.file_operating[_this.file_pointer];
								path = _this.file_path + '/' + $(".select_file_group .file_directory").val();
							break;
							case 2:
								_this.file_pointer = _this.file_pointer - 1
								path = _this.retrun_prev_path(_this.file_path);
							break;
						}
						_this.reader_file_list({path:path,is_operating:false});
					}
				});
		
				//展示已隐藏的目录
				$('.file_path_input .file_dir_view').on('click','.file_dir_omit',function(e){
					var _this = this,new_down_list = $(this).children('.nav_down_list');
					$(this).addClass('active');
					new_down_list.addClass('show');
					$(document).one('click',function(){
						$(_this).removeClass('active');
						new_down_list.removeClass('show');
						e.stopPropagation();
					});
					e.stopPropagation();
				});
				
				// 打开文件夹和文件 --- 双击
				$('#select_dir_list').on('dblclick','tr',function(e){
					if($(e.target).hasClass('file_check')) return false;
					var path = $(this).attr('data-path'),type = $(this).attr('data-type');
					if(type == 'dir'){
						_this.reader_file_list({path:_this.file_path + '/' + path});
					}else{
		
					}
					e.stopPropagation();
					e.preventDefault();
				});
		
				// 文件刷新
				$('.file_path_refresh').click(function(){
					_this.reader_file_list({path:_this.file_path});
				});
		
				// 上传
				$('.file_nav_view .upload_or_download').on('click',function(e){
					_this.open_upload_view();
					e.stopPropagation();
					e.preventDefault();
				});
		
				// 上传与下载下拉点击
				$('.file_nav_view .upload_or_download li').on('click',function(e){
					var type = $(this).data('type')
					if(type === 'uploadFile'){
						_this.open_upload_view();
					}else{
						_this.open_download_view();
					}
					e.stopPropagation();
					e.preventDefault();
				});
		
				// 打开硬盘挂载的目录
				$('.mount_disk_list').on('click','.nav_btn',function(){
					var path = $(this).data('menu');
					_this.reader_file_list({path:path});
				});
		
				// 表头点击事件，触发排序字段和排序方式
				$('.file_list_header').on('click','.file_name,.file_size,.file_mtime,.file_accept,.file_user', function (e) {
					var _tid = $(this).attr('data-tid'),
						_reverse = $(this).find('.icon_sort').hasClass('active'),
						_active = $(this).hasClass('active');
					if (!$(this).find('.icon_sort').hasClass('active') && $(this).hasClass('active')) {
						$(this).find('.icon_sort').addClass('active');
					}else{
						$(this).find('.icon_sort').removeClass('active');
					}
					$(this).addClass('active').siblings().removeClass('active').find('.icon_sort').removeClass('active').empty();
					$(this).find('.icon_sort').html('<i class="iconfont icon-xiala"></i>');
					if (!_active) _reverse = true
					bt.set_cookie('files_sort', _tid);
					bt.set_cookie('name_reverse', _reverse ? 1 : 0);
					_this.reader_file_list();
					return false;
				});
		
				// 设置排序显示
				$('.file_list_header .file_th').each(function (index, item) {
					var files_sort = bt.get_cookie('files_sort'),
						name_reverse = bt.get_cookie('name_reverse');
					if ($(this).attr('data-tid') === files_sort){
						$(this).addClass('active').siblings().removeClass('active').find('.icon_sort').removeClass('active').empty();
						$(this).find('.icon_sort').html('<i class="iconfont icon-xiala"></i>');
						if (name_reverse === 0) $(this).find('.icon_sort').addClass('active');
					}
				});
		
				// 全选选中文件
				$('.file_list_header .file_check').on('click', function (e){
					var checkbox = parseInt($(this).data('checkbox'));
					switch(checkbox){
						case 0:
							$(this).addClass('active').removeClass('active_2').data('checkbox',1);
							$('.file_list_content .file_tr').addClass('active').removeClass('active_2');
							_this.file_table_arry = _this.file_list;
						break;
						case 2:
							$(this).addClass('active').removeClass('active_2').data('checkbox',1);
							$('.file_list_content .file_tr').addClass('active');
							_this.file_table_arry = _this.file_list;
						break;
						case 1:
							$(this).removeClass('active active_2').data('checkbox',0);
							$('.file_list_content .file_tr').removeClass('active');
							_this.file_table_arry = [];
						break;
					}
				});
		
				// 选中文件
				$('.file_list_content').on('click', '.file_check', function (e) { //列表选择
					var _tr = $(this).parents('.file_tr'),index = _tr.data('index'),header_check = $('.file_list_header .file_check'),filename = _tr.attr('data-filename');
					$('.selection_right_menu').removeAttr('style');
					if(_tr.hasClass('active')){
						_tr.removeClass('active');
						_this.remove_check_file(_this.file_table_arry,'filename',filename);
						if(_this.file_table_arry.length > 0){
							header_check.addClass('active_2').removeClass('active').data('checkbox',2);
						}else if(_this.file_table_arry.length == 0){
							header_check.removeClass('active active_2').data('checkbox',0);
						}
					}else{
						_tr.addClass('active');
						_tr.attr('data-filename',_this.file_list[index]['filename']);
						if(_this.file_table_arry.length == _this.file_list.length){
							header_check.addClass('active').removeClass('active_2').data('checkbox',1);
						}else{
							header_check.addClass('active_2').removeClass('active').data('checkbox',2);
						}
						_this.file_table_arry.push(_this.file_list[index]);
					}
					e.stopPropagation();
				});
		
				// 文件列表滚动条事件
				$('.file_list_content').scroll(function(e){
					if($(this).scrollTop() == ($(this)[0].scrollHeight - $(this)[0].clientHeight)){
						$(this).prev().css('opacity',1);
						$(this).next().css('opacity',0);
					}else if($(this).scrollTop() > 0){
						$(this).prev().css('opacity',1);
					}else if($(this).scrollTop() == 0){
						$(this).prev().css('opacity',0);
						$(this).next().css('opacity',1);
					}
				});
		
				// 选中文件
				$('.file_table_view .file_list_content').on('click','.file_tr',function(e){
					$('.selection_right_menu').removeAttr('style');
					$(this).find('.file_checkbox .file_check').click();
					e.stopPropagation();
					e.preventDefault();
				});
		
				// 打开文件夹或文件 --- 文件名单击
				$('.file_table_view .file_list_content').on('click','.file_title i',function(e){
					var file_tr = $(this).parents('.file_tr'),index = file_tr.data('index'),data = _this.file_list[index];
					if(data.type == 'dir'){
						_this.reader_file_list({path:_this.file_path + '/' + data['filename']});
					}else{
		
					}
					e.stopPropagation();
				});
		
				// 打开文件的分享状态
				$('.file_table_view .file_list_content').on('click','.file_name .icon-share1',function(e){
					var file_tr = $(this).parents('.file_tr'),index = file_tr.data('index'),data = _this.file_list[index];
					_this.info_file_share(data,file_tr);
					e.stopPropagation();
				});
		
		
				// 打开文件的收藏夹状态
				$('.file_table_view .file_list_content').on('click','.file_name .icon-favorites',function(e){
					var file_tr = $(this).parents('.file_tr'),index = file_tr.data('index'),data = _this.file_list[index];
					data.typeText = data.type?'文件夹':'文件';
					_this.cancel_file_favorites(data,file_tr);
					e.stopPropagation();
				});
		
		
				// 打开文件夹和文件 --- 双击
				$('.file_table_view .file_list_content').on('dblclick','.file_tr',function(e){
					if($(e.target).hasClass('file_check')) return false;
					var index = $(this).data('index'),data = _this.file_list[index];
					if(data.type == 'dir'){
						
						_this.reader_file_list({path:_this.file_path + '/' + data['filename']});
					}else{
		
					}
					e.stopPropagation();
					e.preventDefault();
				});
		
				// 文件夹和文件鼠标右键
				$('.file_list_content').on('contextmenu','.file_tr',function(ev){
					var _that = this;
					if(ev.which == 3){
						_this.render_file_groud_menu(ev,this);
						$('.content_right_menu').removeAttr('style');
						$(this).addClass('selected').siblings().removeClass('selected');
						$(document).one('click',function(e){
							$(_that).removeClass('selected');
							$('.selection_right_menu').removeAttr('style');
							e.stopPropagation();
							e.preventDefault();
						});
					}
					ev.stopPropagation();
					ev.preventDefault();
				});
		
				// 文件空白区域右键菜单
				$('.file_list_content').on('contextmenu',function(ev){
					var content_right_menu = $('.content_right_menu'),content_menu_width = content_right_menu.width(),content_menu_height = content_right_menu.height(),_that = this;
					if(ev.which == 3){
						$('.selection_right_menu').removeAttr('style');
						_this.render_file_all_menu(ev,this)
					}
					ev.stopPropagation();
					ev.preventDefault();
				});
		
				//设置单页显示的数量，默认为100，设置local本地缓存
				$('.filePage').on('change','.showRow',function(){
					var val = $(this).val();
					bt.set_storage('showRow',val);
					_this.reader_file_list();
				});
		
				// 获取文件夹大小
				$('.file_list_content').on('click','.folder_size',function(e){
					var data =  _this.file_list[$(this).parents('.file_tr').data('index')],_this = this;
					_this.get_file_size({path:data.path},function(res){
						$(_this).text(bt.format_size(res.size));
					});
					e.stopPropagation();
					e.preventDefault();
				});
		
				// 视图调整
				$('.cut_view_model').on('click',function(){
					var type = $(this).data('type');
					$('.file_table_view').addClass(type == 'icon'?'icon_view':'list_view').removeClass(type != 'icon'?'icon_view':'list_view');
					$(this).addClass('active').siblings().removeClass('active');
				});
				
			},
			/**
			 * @description 设置文件前进或后退状态
			 * @returns void
			 */
			set_file_forward:function(){
				var _this = this,forward_path = $('.forward_path span');
				console.log(_this.file_operation)
				if(_this.file_operating.length == 1){
					forward_path.addClass('active');
				}else if(_this.file_pointer == _this.file_operating.length -1){
					forward_path.eq(0).removeClass('active');
					forward_path.eq(1).addClass('active');
				}else if(_this.file_pointer == 0){
					forward_path.eq(0).addClass('active');
					forward_path.eq(1).removeClass('active');
				}else{
					forward_path.removeClass('active');
				}
			},
			/**
			 * @description 设置文件视图
			 * @returns void
			 */
			set_file_view:function(){
				var file_list_content = $('.file_list_content'),height = this.area[1] - 170;
				$('.file_bodys').height(this.area[1] - 100);
				if((this.file_list.length * 50) > height){
					file_list_content.attr('data-height',file_list_content.data('height') || file_list_content.height()).height(height);
					$('.file_shadow_bottom').css('opacity',1);
				}else{
					file_list_content.height(height);
					$('.file_shadow_top,.file_shadow_bottom').css('opacity',0);
				}
			},
			/**
			 * @description 清除表格选中数据和样式
			 * @returns void
			 */
			clear_table_active:function(){
				this.file_table_arry = [];
				$('.file_list_header .file_check').removeClass('active active_2');
				$('.file_list_content .file_tr').removeClass('active');
			},
        }
		select_file.reader_view();
        select_file.event_bind();
	},

    /**
     * @description 请求封装
     * @param {string|object} conifg ajax配置参数/请求地址
     * @param {function|object} callback 回调函数/请求参数
     * @param {function} callback1 回调函数/可为空
     * @returns void 无
    */
    send:function(param1,param2,param3,param4,param5,param6){
		var params = {},success = null,error = null,config = [],param_one = '';
		$.each(arguments,function(index,items){ 
			config.push([items,typeof items]);
		});
		function diff_data(i){
			try {
				success = config[i][1] == "function"?config[i][0]:null;
				error = config[(i+1)][1] == "function"?config[(i+1)][0]:null;
			} catch (error){}
		}
		param_one = config[0];
		switch(param_one[1]){
			case "string":
				$.each(config,function(index,items){
					var value = items[0],type = items[1];
					if(index > 1 && (type == "boolean" || type == "string" || type == "object")){
						var arry = param_one[0].split('/');
						params['url'] = '/'+ arry[0] +'?action=' + arry[1];
						params['load'] = value;
						if(type == "object"){
							params['load'] = value.load;
							params['tips'] = value.tips;
							params['verify'] = value.verify;
						}
						return false;
					}else{
						params['url'] = param_one[0];
					}
				});
				if(config[1][1] === "object"){
					params['data'] = config[1][0];
					diff_data(2);
				}else{
					diff_data(1);
				}
			break;
			case 'object':
				params['url'] = param_one[0].url;
				params['data'] = param_one[0].data || {};
				$.each(config,function(index,items){
					var value = items[0],type = items[1];
					if(index > 1 && (type == "boolean" || type == "string" || type == "object")){
						params['load'] = items;
						if(type == "object"){
							params['load'] = value.load;
							params['tips'] = value.tips;
						}
						return true;
					}
				});
				if(config[1][1] === "object"){
					params['data'] = config[1][0];
					diff_data(2);
				}else{
					diff_data(1);
				}
			break;
		}
		if(params.load) params.load = this.load(params.load);
		$.ajax({
			type:params.type|| "POST",
			url:params.url,
			data:params.data || {},
			dataType: params.dataType || "JSON",
			complete:function(){
				if(params.load) params.load.close();
			},
			success:function (res){
				if(params.verify){
					if(success) success(res);
					return false;
				}
				if(typeof res === "string"){
					layer.msg(res,{icon:2,time:0,closeBtn:2});
					return false;
				}
				if(params.bacth){
					if(success) success(res);
					return false;
				}
				if(res.status === false){
				   bt_tools.msg(res);
				   return false;
				}
				if(params.tips){
					bt_tools.msg(res);
				}
				if(success) success(res);
			},
			error:function(er){
				if(error) error(er);
				layer.closeAll('dialog');
				layer.closeAll('loading');
				layer.msg('Service response error：'+ er.status +'</br>error msg：'+er.statusText+'</br>URL：' + params.url+'</br>param：' + JSON.stringify(params.data) ,{icon:2,time:0,closeBtn:2});
			}
		});
	},
};

$.fn.serializeObject = function(){  
    var hasOwnProperty = Object.prototype.hasOwnProperty;  
    return this.serializeArray().reduce(function(data,pair){  
        if(!hasOwnProperty.call(data,pair.name)){  
            data[pair.name]=pair.value;  
        }  
        return data;  
    },{});  
};
