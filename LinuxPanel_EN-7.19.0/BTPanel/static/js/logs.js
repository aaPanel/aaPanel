var logs = {
	event: function() {
	  var that = this, name = bt.get_cookie('logs_type');
	  that.get_logs_info();
	  // 切换主菜单
	  $('#cutTab').unbind().on('click', '.tabs-item', function () {
		var index = $(this).index(), name = $(this).data('name')
		var parent = $(this).parent().parent().nextAll('.tab-view-box').children('.tab-con').eq(index)
		$(this).addClass('active').siblings().removeClass('active');
		parent.addClass('show w-full').removeClass('hide').siblings().removeClass('show w-full').addClass('hide');
		that[name].event();
		bt.set_cookie('logs_type',name)
	  })
	  $('[data-name="'+ (name || 'panelLogs') +'"]').trigger('click')
	},
	get_logs_info: function () {
		bt_tools.send({url: '/logs/panel/get_logs_info'}, function (rdata) {
			
		})
	},
    // 面板日志
	panelLogs:{
		crontabId: '',
		crontabName: '',
        /**
		 * @description 事件绑定
		 */
		event:function (){
			var that = this;
			$('.state-content').hide()
			$('#panelLogs').unbind('click').on('click','.tab-nav-border span',function(){
			  var index = $(this).index();
			  $(this).addClass('on').siblings().removeClass('on');
			  $(this).parent().next().find('.tab-block').eq(index).addClass('on').siblings().removeClass('on');
			  that.cutLogsTab(index)
			})
			$(window).unbind('resize').resize(function (){
				that.heightResize()
			})
			$('#panelLogs .tab-nav-border span').eq(0).trigger('click');
			$('.refresh_log').unbind('click').on('click',function (){
				that.getLogs(1)
			})
			$('.close_log').unbind('click').on('click',function (){
				that.delLogs()
			})
			$('#panelCrontab .Tab').on('click','.Item',function(){
				var id = $(this).data('id')
				$(this).addClass('active').siblings().removeClass('active')
				that.crontabId = id
				that.crontabName = $(this).prop('title')
				that.get_crontab_logs(id)
			})
			//计划任务日志刷新
			$('.refreshCrontabLogs').unbind('click').click(function (){
				if(!that.crontabId) return layer.msg('No Cron tasks, does not support refresh logs',{icon:2})
				that.get_crontab_logs(that.crontabId)
			})
			//计划任务搜索
			$('#panelLogs .search-input').keyup(function (e) {
				var value = $(this).val()
				if(e.keyCode == 13) that.crontabLogs(value)
			})
			$('#panelLogs').on('click','.glyphicon-search',function(){
				var value = $('#panelLogs .search-input').val()
				that.crontabLogs(value)
			})
		},
		heightResize: function(){
			$('#errorLog .crontab-log').height((window.innerHeight - 310) +'px')
			$('#panelCrontab .crontab-log').height((window.innerHeight - 310) +'px')
			$('#panelCrontab .Tab').css('max-height',(window.innerHeight - 290) +'px')
			$('#panelCrontab').height((window.innerHeight - 240) +'px')
		},
		/**
		 * @description 切换日志菜单
		 * @param {number} index 索引
		 */
		cutLogsTab:function(index){
			switch (index) {
				case 0:
					this.getLogs(1)
					break;
				case 1:
					this.errorLog()
					break;
				case 2:
					this.heightResize()
					this.crontabLogs('',function() {
						$('#panelCrontab .Tab .Item').eq(0).trigger('click');
					})
					break;
			}
		},
		/**
		* @description 获取计划任务执行日志
		* @param {object} id 参数
		*/
		get_crontab_logs: function (id){
			var that = this
			that.getCrontabLogs({id: id}, function (rdata) {
				$('#panelCrontab .crontab-log').html('<code>'+ bt.htmlEncode.htmlEncodeByRegExp(rdata.msg) + '</code>')
				var div = $('#panelCrontab .crontab-log')
				div.height((window.innerHeight - 310) +'px')
				div.scrollTop(div.prop('scrollHeight'))
			})
		},
		/**
		 * @description 计划任务日志
		*/
		crontabLogs:function (search,callback){
			var _that = this
			$('#panelCrontab .Tab').empty()
			bt_tools.send({url: '/data?action=getData&table=crontab',data: {search: search ? search : '',p: 1,limit: 9999}}, function (rdata) {
				$('#panelCrontab .Tab').empty()
				$.each(rdata.data, function (index, item) {
					$('#panelCrontab .Tab').append($('<div class="Item '+ (_that.crontabId && _that.crontabId === item.id ? 'active' : '' ) +'" title="'+ bt.htmlEncode.htmlEncodeByRegExp(item.name) + '" data-id="'+ item.id +'">'+ item.name +'</div>'))
				})
				if(callback) callback(rdata)
			})
		},
		/**
		* @description 获取计划任务执行日志
		* @param {object} param 参数对象
		* @param {function} callback 回调函数
		*/
		getCrontabLogs:function (param,callback){
			var loadT = bt.load('Fetching execution log, please wait...')
			$.post('/crontab?action=GetLogs', { id: param.id }, function (res) {
				loadT.close()
				if (callback) callback(res)
			})
		},
		/**
		 * @description 错误日志
		 */
		errorLog:function (){
			var that = this;
			bt_tools.send({
				url:'/config?action=get_panel_error_logs'},{},function(res){
				log = res.msg
				if(res.data == '') log = 'currently no logs'
				$('#errorLog').html('<div style="font-size: 0;">\
					<button type="button" title="Refresh" class="btn btn-success btn-sm mr5 refreshRunLogs" ><span>Refresh</span></button>\
					<pre class="crontab-log"><code>'+ bt.htmlEncode.htmlEncodeByRegExp(log) +'</code></pre>\
				</div>');
				$('.refreshRunLogs').click(function (){
					that.errorLog()
				})
				var div = $('#errorLog .crontab-log')
				div.height((window.innerHeight - 310) +'px')
				div.scrollTop(div.prop('scrollHeight'))
			},'panel error log')
		},
		/**
		* 取回数据
		* @param {Int} page  分页号
		*/
		getLogs:function(page,search) {
			var that = this
			search = search == undefined ? '':search;
			bt_tools.send({url:'/data?action=getData&table=logs&tojs=getLogs&limit=20&p=' + page+"&search="+search}, function(data) {
				$('#operationLog').empty()
				bt_tools.table({
					el:'#operationLog',
					data: data.data,
                    height: $(window).height() - 330+'px',
                    default: 'Action list is empty', // 数据为空时的默认提示
					tootls: [
						{ // 按钮组
							type: 'group',
							positon: ['left', 'top'],
							list: [{
								title: 'Refresh',
								active: true,
								event: function (ev,_that) {
									that.getLogs(1)
								}
							}, {
								title: 'Clear logs',
								event: function (ev,_that) {
									that.delLogs()
								}
							}]
						}
					],
					column:[
						{ fid: 'username', title: "User",width: 100 },
						{ fid: 'type', title: "Operation type",width: 100 },
						{ fid: 'log', title: "Details",template: function (row) {
							return '<span>'+ (row.log.indexOf('alert') > -1 ? $('<div></div>').text(row.log).html() : row.log) +'</span>'
						}},
						{ fid: 'addtime', title: "Operating time",width: 150}
					],
					success: function () {
						if(!$('#operationLog .search_input').length){
							$('#operationLog .tootls_top').append('<div class="pull-right">\
								<div class="bt_search">\
									<input type="text" class="search_input" style="" placeholder="Please enter log" value="'+ search +'">\
									<span class="glyphicon glyphicon-search" aria-hidden="true"></span>\
								</div>\
							</div>')
							$('#operationLog .search_input').keydown(function (e) {
								var value = $(this).val()
								if(e.keyCode == 13) that.getLogs(1,value)
							})
							$('#operationLog .glyphicon-search').click(function () {
								var value = $('#operationLog .search_input').val()
								that.getLogs(1,value)
							})
						}
					}
				})
				$('.operationLog').html(data.page);
			},'Get panel operation log')
		},
		//清理面板日志
		delLogs: function(){
			var that = this
			bt.firewall.clear_logs(function(rdata){
				layer.msg(rdata.msg,{icon:rdata.status?1:2});
				that.getLogs(1);
			})
		},
    },
    // 网站日志
	siteLogs:{
		siteName: '',
        event: function() {
			var that = this
			this.getSiteList('',function(rdata){
				$('#siteLogs .Tab .Item').eq(0).trigger('click');
			})
			that.heightResize()

			$(window).unbind('resize').resize(function (){
				that.heightResize()
			})

			$('#siteLogs .Tab').unbind().on('click','.Item',function(){
				that.siteName = $(this).data('name')
				$(this).addClass('active').siblings().removeClass('active')
				var index = $('#siteLogs .tab-nav-border span.on').index()
				$('#siteLogs .tab-nav-border span').eq(index).trigger('click');
			})

			$('#siteLogs').unbind().on('click','.tab-nav-border span',function(){
				var index = $(this).index();
				$(this).addClass('on').siblings().removeClass('on');
				$(this).parent().next().find('.tab-block').eq(index).addClass('on').siblings().removeClass('on');
				that.cutLogsTab(index)
			})
			$('#siteLogs .TabGroup .search-input').keyup(function (e) {
				var value = $(this).val()
				if(e.keyCode == 13) that.getSiteList(value)
			})
			$('#siteLogs .TabGroup').on('click','.glyphicon-search',function(){
				var value = $('#siteLogs .search-input').val()
				that.getSiteList(value)
			})
        },
		heightResize: function(){
			$('#siteLogs .Tab').css('max-height',(window.innerHeight - 290) +'px')
			$('#siteLogs').height((window.innerHeight - 200) +'px')
			$('#siteOnesite .divtable').css('max-height',($(window).height() - 350) +'px')
			$('#siteRun .crontab-log').height((window.innerHeight - 330) +'px')
			$('#siteError .crontab-log').height((window.innerHeight - 330) +'px')
		},
		/**
		 * @description 获取网站列表
		*/
		getSiteList:function(search,callback){
			var that = this
			$('#siteLogs .Tab').empty()
			bt_tools.send('/data?action=getData&table=sites',{limit: 999999,p:1,search: search ? search : '',type: -1},function(rdata){
				var _html = ''
				$.each(rdata.data,function(index,item){
					_html += '<div class="Item '+ (that.siteName && that.siteName === item.name ? 'active' : '' ) +'" title="'+ item.name+'（'+ item.ps +'）' +'" data-name="'+ item.name +'">'+ item.name+(item.ps ? '（'+ item.ps +'）' : '') +'</div>'
				})
				$('#siteLogs .Tab').html(_html)
				if(callback) callback(rdata)
			})
		},
		/**
		 * @description 切换日志菜单
		 * @param {number} index 索引
		*/
		cutLogsTab:function(index){
			var that = this;
			switch (index) {
				case 0://网站操作日志 
					that.getSiteOnesite();
					break;
				case 1://网站运行日志
					that.getSiteRun()
					break;
				case 2://网站错误日志
					that.getSiteError()
					break;
				case 3://WEB日志分析
					that.getSiteWeb()
					break;
			}
		},
		/**
		 * @description 获取网站操作日志
		*/
		getSiteOnesite: function(p) {
			var that = this;
			$('#siteOnesite').empty()
			bt_tools.table({
				el: '#siteOnesite',
				url: '/logs/panel/get_logs_bytype',
				param: { 
					data: JSON.stringify({
						stype: 'Site manager',
						search: that.siteName,
						limit: 20,
						p: p || 1
				})
				},
				height: $(window).height() - 350,
				dataFilter: function(res) {
					$('#siteOnesite .tootls_bottom').remove()
					$('#siteOnesite').append('<div class="tootls_group tootls_bottom"><div class="pull-right"></div></div>')
					$('#siteOnesite .tootls_bottom .pull-right').append($(res.page).addClass('page'))
					$('#siteOnesite .tootls_bottom .pull-right .page').on('click','a',function(e){
						var num = $(this).prop('href').split('p=')[1]
						that.getSiteOnesite(num)
						e.preventDefault();
					})
					return {data: res.data}
				},
				tootls: [
					{ // 按钮组
					  type: 'group',
					  positon: ['left', 'top'],
					  list: [{
						title: 'Refresh',
						active: true,
						event: function (ev,_that) {
							_that.$refresh_table_list(true)
						}
					  }]
					}
				],
				column: [
					{fid: 'username', title: 'User', type: 'text', width: 150},
					{fid: 'type', title: 'Operation type', type: 'text', width: 150},
					{fid: 'log', title: 'Log', type: 'text', width: 300},
					{fid: 'addtime', title: 'Operation time', type: 'text', width: 150},
				]
			})
		},
		/**
		 * @description 网站运行日志
		*/
		getSiteRun: function(search,p) {
			var that = this;
			console.log('------');
			var loadT = bt.load('Fetching logs, please wait...')
			$.post('/site?action=GetSiteLogs', { siteName: that.siteName}, function (rdata) {
				loadT.close();
				$('#siteRun').html('<div style="margin-bottom: 5px; position: relative; height:30px;line-height:30px;display: flex;justify-content: space-between;"><button type="button" title="Refresh" class="btn btn-success btn-sm mr15 refreshSiteSunLogs" >\
					<span>Refresh</span></button>\
				</div>\
				<div style="font-size: 0;">\
					<pre class="crontab-log"><code>'+ bt.htmlEncode.htmlEncodeByRegExp(rdata.msg === "" ? 'currently no logs.' : rdata.msg) +'</code></pre>\
				</div>');

				$('.refreshSiteSunLogs').click(function (){
					that.getSiteRun()
				})
				var div = $('#siteRun .crontab-log')
				div.height((window.innerHeight - 330) +'px')
				div.scrollTop(div.prop('scrollHeight'))
			})
		},
		/**
		 * @description 网站错误日志
		*/
		getSiteError: function() {
			var that = this;
			bt.site.get_site_error_logs(that.siteName, function (rdata) {
				$('#siteError').html('<div style="font-size: 0;">\
					<button type="button" title="Refresh" class="btn btn-success btn-sm mr5 refreshSiteErrorLogs" ><span>Refresh</span></button>\
					<pre class="crontab-log"><code>'+ bt.htmlEncode.htmlEncodeByRegExp(rdata.msg) +'</code></pre>\
				</div>');

				$('.refreshSiteErrorLogs').click(function (){
					that.getSiteError()
				})

				var div = $('#siteError .crontab-log')
				div.height((window.innerHeight - 330) +'px')
				div.scrollTop(div.prop('scrollHeight'))
			})
		},
		/**
		 * @description WEB日志分析
		*/
		getSiteWeb: function() {
			var that = this,robj = $('#siteWeb');
			var progress = '';  //扫描进度
			robj.empty()
			var loadT = bt.load('Fetching log analysis data, please wait...');
			$.post('/ajax?action=get_result&path=/www/wwwlogs/' + that.siteName+'.log', function (rdata) {
				loadT.close();
				//1.扫描按钮
				var analyes_log_btn = '<button type="button" title="Log scan" class="btn btn-success analyes_log btn-sm mr5"><span>Log scan</span></button>'

				//2.功能介绍
				var analyse_help = '<ul class="help-info-text c7">\
					<li>Log security analysis: scan website (.log) logs containing attack type requests (types include：<em style="color:red">xss,sql,san,php</em>)</li>\
					<li>Analyzed log data contains intercepted requests</li>\
					<li>By default, the last scan data is displayed (if not, please click log scan)</li>\
					<li>If the log file is too large, the scan may take a long time, please be patient</li>\
					<li> <a href="https://www.aapanel.com/forum/d/3351-nginx-waf-instructions" style="color: #20a53a;" target="_blank">aaPanel WAF </a> can effectively block such attacks</li>\
					</ul>'

				robj.append(analyes_log_btn+'<div class="analyse_log_table"></div>'+analyse_help)
				render_analyse_list(rdata);

				//事件
				$(robj).find('.analyes_log').click(function(){
					bt.confirm({
						title:'Scan website logs',
						msg:'It is recommended to conduct security analysis when the server load is low. This time, the【'+that.siteName+'.log】file will be scanned, and the waiting time may be longer. Do you want to continue?'
					}, function(index){
						layer.close(index)
						progress = layer.open({
							type: 1,
							closeBtn: 2,
							title: false,
							shade: 0,
							area: '400px',
							content: '<div class="pro_style" style="padding: 20px;"><div class="progress-head" style="padding-bottom: 10px;">Scanning, scan progress...</div>\
									<div class="progress">\
										<div class="progress-bar progress-bar-success progress-bar-striped" role="progressbar" aria-valuenow="40" aria-valuemin="0" aria-valuemax="100" style="width: 0%">0%</div>\
									</div>\
								</div>',
							success:function(){
								// 开启扫描并且持续获取进度
								$.post('/ajax?action=log_analysis&path=/www/wwwlogs/' + that.siteName+'.log', function (rdata) {
									if(rdata.status){
										detect_progress();
									}else{
										layer.close(progress);
										layer.msg(rdata.msg, { icon: 2, time: 0, shade: 0.3, shadeClose: true });
									}
								})
							}
						})
					})
				})
			})
			// 渲染分析日志列表
			function render_analyse_list(rdata){
				console.log(rdata);
				var numTotal = rdata.xss+rdata.sql+rdata.san+rdata.php+rdata.ip+rdata.url
				var analyse_list = '<div class="divtable" style="margin-top: 10px;"><table class="table table-hover">\
					<thead><tr><th width="142">Scan time</th><th>times</th><th>XSS</th><th>SQL</th><th>Scan</th><th>PHP attack</th><th>IP(top100)</th><th>URL(top100)</th><th>total</th></tr></thead>\
					<tbody class="analyse_body">'
				if(rdata.is_status){   //检测是否有扫描数据
					analyse_list +='<tr>\
							<td>'+rdata.start_time+'</td>\
							<td>'+rdata.time.substring(0,4)+' Sec</td>\
							<td class="onChangeLogDatail" '+(rdata.xss>0?'style="color:red"':'')+' name="xss">'+rdata.xss+'</td>\
							<td class="onChangeLogDatail" '+(rdata.sql>0?'style="color:red"':'')+' name="sql">'+rdata.sql+'</td>\
							<td class="onChangeLogDatail" '+(rdata.san>0?'style="color:red"':'')+' name="san">'+rdata.san+'</td>\
							<td class="onChangeLogDatail" '+(rdata.php>0?'style="color:red"':'')+' name="php">'+rdata.php+'</td>\
							<td class="onChangeLogDatail" '+(rdata.ip>0?'style="color:#20a53a"':'')+' name="ip">'+rdata.ip+'</td>\
							<td class="onChangeLogDatail" '+(rdata.url>0?'style="color:#20a53a"':'')+' name="url">'+rdata.url+'</td>\
							<td>'+numTotal+'</td>\
						</tr>'
				}else{
					analyse_list+='<tr><td colspan="9" style="text-align: center;">no scan data</td></tr>'
				}
				analyse_list += '</tbody></table></div>'
				$('.analyse_log_table').html(analyse_list)
				$('.onChangeLogDatail').css('cursor','pointer').attr('title','Click for details')
				//查看详情
				$('.onChangeLogDatail').on('click',function(){
					get_analysis_data_datail($(this).attr('name'))
				})
			}
			// 扫描进度
			function detect_progress(){
				$.post('/ajax?action=speed_log&path=/www/wwwlogs/' + that.siteName+'.log', function (res) {
					var pro = res.msg
					if(pro !== 100){
						if (pro > 100) pro = 100;
						if (pro !== NaN) {
							$('.pro_style .progress-bar').css('width', pro + '%').html(pro + '%');
						}
						setTimeout(function () {
							detect_progress();
						}, 1000);
					}else{
						layer.msg('scan complete',{icon:1,timeout:4000})
						layer.close(progress);
						get_analysis_data();
					}
				})
			}
			// 获取扫描结果
			function get_analysis_data(){
				var loadTGA = bt.load('Fetching log analysis data, please wait...');
				$.post('/ajax?action=get_result&path=/www/wwwlogs/' + that.siteName+'.log', function (rdata) {
					loadTGA.close();
					render_analyse_list(rdata,true)
				})
			}
			// 获取扫描结果详情日志
			function get_analysis_data_datail(name){
				layer.open({
					type: 1,
					closeBtn: 2,
					shadeClose: false,
					title: '【'+name+'】log details',
					area: '650px',
					content:'<pre id="analysis_pre" style="background-color: #333;color: #fff;height: 545px;margin: 0;white-space: pre-wrap;border-radius: 0;"></pre>',
					success: function () {
						var loadTGD = bt.load('Fetching log detail data, please wait...');
						$.post('/ajax?action=get_detailed&path=/www/wwwlogs/' + that.siteName+'.log&type='+name+'', function (logs) {
							loadTGD.close();
							$('#analysis_pre').text((name == 'ip' || name == 'url' ? ' [Access Times] [' + name + '] \n' : '') + logs);
						})
					}
				})
			}
		},
		check_log_time: function () {
            bt.confirm({
                msg: "是否立即校对IIS日志时间，校对后日志统一使用北京时间记录？",
                title: 'Hint'
            }, function () {
                var loading = bt.load()
                bt.send("check_log_time", 'site/check_log_time', {}, function (rdata) {
                    loading.close();
                    if (rdata.status) {
                        site.reload();
                    }
                    bt.msg(rdata);
                })
            })
        },
    },
	// 日志审计
  logAudit:{

    data:{},
    /**
     * @description SSH管理列表
     */
    event:function (){
      var that = this;
      $('#logAudit .logAuditTab').empty()
      this.getLogFiles()
      $('.state-content').hide()
			var pro = parseInt(bt.get_cookie('pro_end'))
			if(pro < 0) {
				$('#logAudit .installSoft').show().prevAll().hide()
			}else{
				$('#logAudit').height($(window).height() - 180)
				$(window).unbind('resize').on('resize', function () {
					var height = $(window).height() - 180;
					$('#logAudit').height(height)
					$('#logAuditTable .divtable').css('max-height', height - 150)
				})
			}
      $('.logAuditTab').unbind('click').on('click', '.logAuditItem',function (){
        var data = $(this).data(), list = []
        $.each(data.list, function (key, val){
          list.push(val.log_file)
        })
        $(this).addClass('active').siblings().removeClass('active');
        that.getSysLogs({log_name: data.log_file, list: list, p:1})
      })

      $('#logAuditPages').unbind('click').on('click', 'a', function (){
        var page = $(this).data('page')
        that.getSysLogs({log_name: that.data.log_name, list: that.data.list, p: page})
        return false
      })
    },

    /**
     * @description 获取日志审计类型
     */
    getLogFiles: function () {
      var that = this;
      bt_tools.send({
        url: '/safe/syslog/get_sys_logfiles'
      }, function (rdata) {
        if(rdata.hasOwnProperty('status') ){
          if(!rdata.status && rdata.msg.indexOf('professional member only') > -1){
            $('.logAuditTabContent').hide();
            $('#logAudit .installSoft').show()
            return false
          }
        }
        var initData = rdata[0], list = []
        $.each(rdata, function (i, v) {
          var logSize = 0;
          $.each(v.list,function (key, val){
            logSize += val.size;
          })
          $('#logAudit .logAuditTab').append($('<div class="logAuditItem" title="'+ (v.name + ' - '+ v.title +'('+ ToSize(v.size)) +'" data-file="'+ v.log_file +'">' + v.name + ' - '+ v.title +'('+ ToSize(v.size + logSize) +')</div>').data(v))
        })
        $('#logAudit .logAuditTab .logAuditItem:eq(0)').trigger('click')
      }, {load:'Get the log audit type',verify:false})
    },

    /**
     * @description 获取日志审计类型列表
     */
    getSysLogs: function (param) {
      var that = this;
      var page = param.p || 1;
      that.data = { log_name: param.log_name, list: param.list, limit: 20, p: page }
      bt_tools.send({
        url: '/safe/syslog/get_sys_log',
        data: {data:JSON.stringify(that.data)}
      }, function (rdata) {
        if(typeof rdata[0] === 'string'){
					$('#logAuditPre').show().siblings().hide()
          that.renderLogsAuditCommand(rdata)
        }else{
					console.log(1);
          $('#logAuditTable,#logAuditPages').show()
          $('#logAuditPre').hide()
          that.renderLogsAuditTable({ p:page }, rdata)
        }
      }, {
        load: 'Get a list of log audit types',
        verify: false
      })
    },

    /**
     * @description 渲染日志审计命令
     * @param {Object} rdata 参数
     */
    renderLogsAuditCommand: function (rdata) {
      var logAuditLogs = $('#logAuditPre');
      var str = rdata.join('\r').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
      logAuditLogs.html('<pre style="height: 600px; background-color: #333; color: #fff; overflow-x: hidden; word-wrap:break-word; white-space:pre-wrap;"><code>' + str + '</code></pre>');
      logAuditLogs.find('pre').scrollTop(9999999999999).css({height: $(window).height() - 180})
    },

    /**
     * @description 渲染日志审计表格
     * @param {object} param 参数
     */
    renderLogsAuditTable: function (param, rdata){
      var that = this;
      var column = [], data = rdata[0] ? rdata[0] : { Time: '--', 'Role': '--', 'Event': '--'}, i = 0;
      $.each(data, function (key) {
        // console.log(key === '时间',i)
        column.push({ title: key, fid: key,width: (key === 'Time' &&  i === 0) ? '200px' : (key === 'Time'?'300px':'') })
        i++;
      })
      $('#logAuditTable').empty()
      return bt_tools.table({
        el: '#logAuditTable',
        url:'/safe/syslog/get_sys_log',
        load: 'Get log audit content',
        default: 'log is empty', // 数据为空时的默认提示
        column: column,
        dataFilter: function (data) {
          if(typeof data.status === "boolean" && !data.status){
            $('.logAuditTabContent').hide().next().show();
            return { data: [] }
          }
          if(typeof data[0] === 'string'){
            $('#logAuditPre').show().siblings().hide()
            that.renderLogsAuditCommand(rdata)
          }else{
            $('#logAuditTable,#logAuditPages').show()
            $('#logAuditPre').hide()
            return {data:data}
          }
        },
        beforeRequest: function (param) {
          delete  param.data
          return {data:JSON.stringify($.extend(that.data,param))}
        },
        tootls: [{ // 按钮组
          type: 'group',
          list: [{
            title: 'Refresh',
            active: true,
            event: function (ev) {
              that.getSysLogs(that.data)
            }
          }]
        },{ // 搜索内容
          type: 'search',
          placeholder: 'Please enter Source/Port/Role/Event',
          searchParam: 'search', //搜索请求字段，默认为 search
        },{
          type:'page',
          number:20
        }],
        success:function (config){
          $('#logAuditTable .divtable').css('max-height', $(window).height()  - 280)
        }
      })
    }
  },
	// SSH登录日志
	loginLogs:{
    event: function() {
			var that = this;
			var pro = parseInt(bt.get_cookie('pro_end'))
			if(pro < 0) {
        return $('#loginLogsContent').hide().next().show();
      }
			var type = $('.cutLoginLogsType button.btn-success').data('type')
			this.loginLogsTable({p:1, type: type? type : 0});
			 // 切换登录日志类型
			$('#loginLogsContent').unbind('click').on('click','.cutLoginLogsType button',function(){
				var type = $(this).data('type');
				$(this).addClass('btn-success').removeClass('btn-default').siblings().addClass('btn-default').removeClass('btn-success');
				// $('#loginLogsContent>div:eq('+ type +')').show().siblings().hide();
				that.loginLogsTable({p:1,type: Number(type)});
			})
        },
		/**
     * @description 登录日志
     */
    loginLogsTable:function(param){
      if(!param) param = { p:1, type:0 };
      var logsArr = [['ALL','Logs'],['Accepted','Success log'],['Failed','Failure log']];
      var type = logsArr[param.type][0] , tips = logsArr[param.type][1];
			param.type = type;
      var that = this;
      $('#loginAllLogs').empty();
      var arry = ['ALL','Success','Failure'];
			var html = $('<div class="btn-group mr10 cutLoginLogsType"></div>');
      $.each(arry,function (i,v){
        html.append('<button type="button" class="btn btn-sm btn-'+ (logsArr[i][0] === param.type ?'success':'default') +'" data-type="'+ i +'">'+ v +'</button>')
      })
			param['select'] = param.type
			delete param.type
      return bt_tools.table({
        el: '#loginAllLogs',
				url: '/safe/syslog/get_ssh_list',
        load: 'Get SSH login' + tips,
        default: 'SSH login'+ tips +'is empty', // 数据为空时的默认提示
        autoHeight: true,
        param:param,
        dataVerify:false,
        tootls: [
          { // 按钮组
            type: 'group',
            list: [{
              title: 'Refresh',
              active: true,
              event: function (ev,that) {
                that.$refresh_table_list(true)
              }
            }]
          },
          { // 搜索内容
            type: 'search',
            placeholder: 'Please enter IP/User',
            searchParam: 'search', //搜索请求字段，默认为 search
          },{ //分页显示
            type: 'page',
            positon: ['right', 'bottom'], // 默认在右下角
            pageParam: 'p', //分页请求字段,默认为 : p
            page: 1, //当前分页 默认：1
            numberParam: 'limit',
            //分页数量请求字段默认为 : limit
            number: 20,
            //分页数量默认 : 20条
            numberList: [10, 20, 50, 100, 200], // 分页显示数量列表
            numberStatus: true, //　是否支持分页数量选择,默认禁用
            jump: true, //是否支持跳转分页,默认禁用
          }
        ],
        beforeRequest: function (data) {
          if(typeof data.data === "string"){
            delete data.data
            return {data: JSON.stringify(data)}
          }
          return {data: JSON.stringify(data)}
        },
        column: [
          {title: 'IP: port',fid: 'address',width:'150px', template:function (row){
              return '<span>'+ row.address +':' + row.port + '</span>';
            }},
          // {title: '登录端口',fid: 'port'},
          {title: 'Place of attribution',template:function (row){
              return '<span>'+ (row.area?'' + row.area.info + '':'-') +'</span>';
            }},
          {title: 'User',fid: 'user'},
          {title: 'Failure', template: function (item) {
              var status = Boolean(item.status);
              return '<span style="color:'+ (status?'#20a53a;':'red') +'">'+ (status ? 'Success' : 'Failure') +'</span>';
            }},
          {title: 'Time', fid: 'time', width:150}
        ],
        success:function (config){
          $(config.config.el + ' .tootls_top .pull-right').prepend(html)
        }
      })
    },
  },
	//软件日志
	softwareLogs: {
		username: '',
		/**
		 * @description 事件绑定
		 */
		 event:function (){
			var that = this;
			$('#softwareLogs').unbind('click').on('click','.tab-nav-border span',function(){
			  var index = $(this).index();
			  $(this).addClass('on').siblings().removeClass('on');
			  $(this).parent().next().find('.tab-block').eq(index).addClass('on').siblings().removeClass('on');
			  that.cutLogsTab(index)
			})
			$('#softwareLogs .tab-nav-border span').eq(0).trigger('click');

			$('#softwareLogs .TabGroup .search-input').keyup(function (e) {
				var value = $(this).val()
				if(e.keyCode == 13) that.getFtpList(value)
			})
			$('#softwareLogs .TabGroup').on('click','.glyphicon-search',function(){
				var value = $('#softwareLogs .search-input').val()
				that.getFtpList(value)
			})
			$('#softwareLogs .Content .search-input').keyup(function (e) {
				var value = $(this).val()
				if(e.keyCode == 13) that.getFtpLogs(value)
			})
			$('#softwareLogs .Content').on('click','.glyphicon-search',function(){
				var value = $('#softwareLogs .Content .search-input').val()
				that.getFtpLogs(value)
			})
			$('#softwareLogs .Tab').unbind().on('click','.Item',function(){
				that.username = $(this).data('username')
				$(this).addClass('active').siblings().removeClass('active')
				that.getFtpLogs()
			})
			$('.refreshFtpLogs').click(function (){
				that.getFtpLogs()
			})
			$('#softwareMysqlSlow .search-input').keyup(function (e) {
				var value = $(this).val()
				if(e.keyCode == 13) that.getMysqlSlowLogs(value)
			})
			$('#softwareMysqlSlow').on('click','.glyphicon-search',function(){
				var value = $('#softwareMysqlSlow .search-input').val()
				that.getMysqlSlowLogs(value)
			})
			$('.refreshMysqlSlow').click(function (){
				that.getMysqlSlowLogs()
			})
			$('.refreshMysqlError').click(function (){
				that.getMysqlErrorLogs()
			})
			$(window).unbind('resize').resize(function (){
				that.heightResize()
			})
			that.heightResize()
			// 切换日志类型
			$('#ftpLogsTable').unbind('click').on('click','.cutFtpLogsType button',function(){
				var type = $(this).data('type');
				$(this).addClass('btn-success').removeClass('btn-default').siblings().addClass('btn-default').removeClass('btn-success');
				that.getFtpLogs({p:1,type: Number(type)});
			})
		},
		heightResize: function(){
			$('#softwareFtp .Tab').css('max-height',(window.innerHeight - 300) +'px')
			$('#softwareLogs').height((window.innerHeight - 200) +'px')
			$('#softwareLogs .crontab-log').height((window.innerHeight - 330) +'px')
		},
		/**
		 * @description 切换日志菜单
		 * @param {number} index 索引
		 */
		cutLogsTab:function(index){
			var that = this;
			switch (index) {
				case 0://FTP日志
					var pro = parseInt(bt.get_cookie('pro_end'))
					if(pro < 0){
						return $('#softwareFtp .daily-thumbnail').show().prev().hide()
					}
					that.getFtpList('',function(rdata){
						$('#softwareLogs .Tab .Item').eq(0).trigger('click');
					})
					break;
				case 1://MySql慢日志
					that.getMysqlSlowLogs()
					break;
				case 2://MySql错误日志
					that.getMysqlErrorLogs()
					break;
			}
		},
		/**
		 * @description MySql慢日志
		*/
		getMysqlSlowLogs:function(search,limit){
			limit = limit || 5000;
			var loadT = bt.load('Fetching MySql slow logs, please wait...')
			$.post('/logs/panel/get_slow_logs',{data:JSON.stringify({search:search,limit: limit})},function (rdata) {
				loadT.close()
				$('#softwareMysqlSlow .crontab-log').html('<code>'+ bt.htmlEncode.htmlEncodeByRegExp(rdata['msg'] ? rdata.msg : (rdata.length ? rdata.join('\n') : 'No log information.') + '</code>'))
				var div = $('#softwareMysqlSlow .crontab-log')
				div.height((window.innerHeight - 330) +'px')
				div.scrollTop(div.prop('scrollHeight'))
			})
		},
		/**
		 * @description MySql错误日志
		*/
		getMysqlErrorLogs:function(){
			var loadT = bt.load('Fetching MySql slow logs, please wait...')
			$.post('/database?action=GetErrorLog', function (rdata) {
				loadT.close()
				$('#softwareMysqlError .crontab-log').html('<code>'+ bt.htmlEncode.htmlEncodeByRegExp(rdata ? rdata : 'No log information.') +'</code>')
				var div = $('#softwareMysqlError .crontab-log') 
				div.height((window.innerHeight - 330) +'px')
				div.scrollTop(div.prop('scrollHeight'))
			}) 
		},
		/**
		 * @description 获取FTP日志
		 * @param {string} param 搜索内容
		 */
		getFtpLogs:function(param){
			var that = this;
			console.log(param)
			if(!param) param = { p:1, type:0 };
      var logsArr = [['Login logs','get_login_logs'],['Operation logs','get_action_logs']];
      $('#ftpLogsTable').empty();
      var arry = ['Login','Operation'];
			var span = $('<span style="border-left: 1px solid #ccc;margin: 0 15px;"></span><span class="mr5">Logs type：</span>');
      var html = $('<div class="btn-group mr10 cutFtpLogsType" style="top: -2px;"></div>');
      $.each(arry,function (i,v){
        html.append('<button type="button" class="btn btn-sm btn-'+ (i === param.type ?'success':'default') +'" data-type="'+ i +'">'+ v +'</button>')
      })
			if(param.type == 0){
				return bt_tools.table({
					el: '#ftpLogsTable',
					url: '/ftp?action='+ logsArr[param.type][1],
					default: 'No log information, If FTP log not enabled, please go to [ App Store ] - [ Pure-Ftpd ] - [ Logs Manage ] enabled',
					height: 390,
					param: {
						user_name: that.username
					},
					column: [
						{ title: 'User', type: 'text', width: 100,template:function() {
							return '<span>' + that.username + '</span>';
						}},
						{ fid: 'ip', title: 'Login IP', type: 'text', width: 110},
						{ fid: 'status', title: 'Status', type: 'text', width: 75,
						template: function (rowc, index, ev) {
								var status = rowc.status.indexOf('Success') > -1
							return '<span class="' + (status ?  'btlink' : 'bterror' ) + '">' + (status ?  'Success' : 'Failure' ) + '<span>';
						}},
						{ fid: 'in_time', title: 'Login time', type: 'text', width: 150 },
						{ fid: 'out_time', title: 'logout time', type: 'text', width: 200},
					],
					tootls: [
						{
							type:'group',
							positon:['left','top'],
							list:[
								{title:'Refresh',active:true,event:function(ev,ethat){
										$('#bt_ftp_Login_logs .search_input').val('')
										ethat.config.search.value = ''
									ethat.$refresh_table_list(true)
								}},
							]
						},
						{
							type: 'search',
							positon: ['right', 'top'],
							placeholder: 'Please enter Login IP/Status/Time',
							searchParam: 'search', //搜索请求字段，默认为 search
							value: '',// 当前内容,默认为空
						},
						{
							type: 'page',
							positon: ['right', 'bottom'], // 默认在右下角
							pageParam: 'p', //分页请求字段,默认为 : p
							page: 1, //当前分页 默认：1
						}
					],
					success:function(){
						$('#ftpLogsTable .tootls_top .pull-left').append(span).append(html)
					}
				})
			}else{
				var typeList = [
					{ title: 'all', value: 'all' },
					{ title: 'upload', value: 'upload' },
					{ title: 'upload', value: 'upload' },
					{ title: 'delete', value: 'delete' },
					{ title: 'rename', value: 'rename' }]
				table_logsOperation('all')
				function table_logsOperation(type) {
					$('#ftpLogsTable').empty()
					bt_tools.table({
						el: '#ftpLogsTable',
						default: 'No log information',
						height: 350,
						url: '/ftp?action='+ logsArr[param.type][1],
						param: {
							user_name: that.username,
							type: type
						},
						column: [
							{ title: 'User', type: 'text', width: 100,template:function() {
								return '<span>' + that.username + '</span>';
							}},
							{ fid: 'ip', title: 'Operation IP', type: 'text', width: 110},
							{ fid: 'file', title: 'File', type: 'text', width: 240,fixed: true },
							{ fid: 'type', title: 'Type', type: 'text', width: 75},
							{ fid: 'time', title: 'Time', type: 'text', width: 100 },
						],
						tootls: [{
								type:'group',
								positon:['left','top'],
								list:[
									{title:'Refresh',active:true,event:function(){
										table_logsOperation(type)
									}},
								]
							},
							{
								type: 'search',
								positon: ['right', 'top'],
								placeholder: 'Please enter IP/File/Type/Time',
								searchParam: 'search', //搜索请求字段，默认为 search
								value: '',// 当前内容,默认为空
							},
							{
								type: 'page',
								positon: ['right', 'bottom'], // 默认在右下角
								pageParam: 'p', //分页请求字段,默认为 : p
								page: 1, //当前分页 默认：1
							}
						],
						success: function () {
							if(!$('#ftpLogsTable .log_type').length){
								var _html = ''
								$.each(typeList, function (index, item) {
									_html += '<option value="' + item.value + '">' + item.title + '</option>'
								})
								$('#ftpLogsTable .bt_search').before('<select class="bt-input-text mr5 log_type" style="width:110px" name="log_type">'+ _html +'</select>')
								$('#ftpLogsTable .tootls_top .pull-left').append(span).append(html)
								$('#ftpLogsTable .log_type').val(type)
								$('#ftpLogsTable .log_type').change(function () {
									table_logsOperation($(this).val())
								})
							}
						}
					})
				}
			}
		},
		/**
		 * @description 获取网站列表
		*/
		getFtpList:function(search,callback){
			var that = this
			$('#softwareFtp .Tab').empty()
			bt_tools.send('/data?action=getData&table=ftps',{limit: 999999,p:1,search: search ? search : ''},function(rdata){
				var _html = ''
				$.each(rdata.data,function(index,item){
					_html += '<div class="Item '+ (that.username && that.username === item.name ? 'active' : '' ) +'" title="'+ item.name+'（'+ item.ps +'）' +'" data-username="'+ item.name +'">'+ item.name+'（'+ item.ps +'）' +'</div>'
				})
				$('#softwareFtp .Tab').html(_html)
				if(callback) callback(rdata)
			})
		},
	},
	/**
	 * @description 渲染日志分页
	 * @param pages
	 * @param p
	 * @param num
	 * @returns {string}
	*/
	renderLogsPages:function(pages,p,num){
		return (num >= pages?'<a class="nextPage" data-page="1">Home</a>':'') + (p !== 1?'<a class="nextPage" data-page="'+ (p-1) +'">Prev</a>':'') + (pages <= num?'<a class="nextPage" data-page="'+ (p+1) +'">Next</a>':'')+'<span class="Pcount">第 '+ p +' page</span>';
	}
}
logs.event();

//面板操作日志分页切换
function getLogs(page) {
	logs.panelLogs.getLogs(page,$('#operationLog .search_input').val())
}
