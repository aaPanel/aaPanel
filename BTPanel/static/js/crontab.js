var backupListAll = [], siteListAll = [], databaseListAll = [], allDatabases = [],allTables = [],
    backuptolist = [{ title: 'Local disk', value: 'localhost' },
      // { title: '阿里云OSS', value: 'alioss' },
      // { title: '腾讯云COS', value: 'txcos' },
      // { title: '七牛云存储', value: 'qiniu' },
      // { title: '华为云存储', value: 'obs' },
      // { title: '百度云存储', value: 'bos' }];
     ];
var crontab = {
  typeTips: { site: 'Backup Site', database: 'Backup Database', logs: 'Cut Log', path: 'Backup Directory' },
  crontabForm: { name: '', type: '', where1: '', hour: '', minute: '', week: '', sType: '', sBody: '', sName: '', backupTo: '', save: '', sBody: '', urladdress: '', save_local: '', notice: '', notice_channel: '' , datab_name : '',tables_name :'' },
  editForm: false,
	crontabFormConfig: [{
    label: 'Type of Task',
    group: {
      type: 'select',
      name: 'sType',
      width: '180px',
      value: 'toShell',
      list: [
        { title: 'Shell Script', value: 'toShell' },
        { title: 'Backup Site', value: 'site' },
        { title: 'Backup Database', value: 'database' },
        // { title: '数据库增量备份', value: 'enterpriseBackup' },
        { title: 'Cut Log', value: 'logs' },
        { title: 'Backup Directory', value: 'path' },
        // { title: '木马查杀', value: 'webshell' },
        { title: 'Sync time', value: 'syncTime' },
        { title: 'Free RAM', value: 'rememory' },
        { title: 'Access URL', value: 'toUrl' }
      ],
      unit: '<span style="margin-top: 9px; display: inline-block;"><i style="color: red;font-style: initial;font-size: 12px;margin-right: 5px">*</i>Type of task: Shell Script, Backup Site, Backup Database, Cut log, Free RAM, Access URL, Sync time</span>\
			<span style="display:inline-block; margin-left:10px;vertical-align: middle;" class="feedback-btn"><span class="flex" style="align-items: center;margin-right:16px;width:100px;"><i class="icon-demand"></i><a class="btlink" onClick="javascript:bt.openFeedback({title:\'aaPanel demand feedback collection\',placeholder:\'<span>If you encounter any problems or imperfect functions during use, please describe <br> your problems or needs to us in detail, we will try our best to solve or improve for <br> you</span>\',recover:\'We pay special attention to your requirements feedback, and we conduct regular weekly requirements reviews. I hope I can help you better\',key:993,proType:2});" style="margin-left: 5px;">Feedback</a></span></span>',
      change: function (formData, element, that) {
        that.data.type = 'week'   //默认类型为每星期
        var config = crontab.crontabsType(arryCopy(crontab.crontabFormConfig), formData, that)
        that.$again_render_form(config)
        var arry = ['site', 'database', 'logs', 'webshell', 'enterpriseBackup'];
        if (arry.indexOf(formData.sType) > -1) {
          that.$replace_render_content(3)
          setTimeout(function () {
            $('[data-name="sName"] li:eq(0)').click()
          }, 100)
        }
        if (formData.sType === 'enterpriseBackup') {
          console.log('---')
          $('.glyphicon-repeat').on('click',function(){
            that.config.form[6].group.value = bt.get_random(bt.get_random_num(6,10))
            that.$local_refresh('urladdress', that.config.form[6].group)
            $('input[name=urladdress]').click()
          })
        }
      }
    }
  }, {
    label: 'Name of Task',
    group: {
      type: 'text',
      name: 'name',
      width: '350px',
      placeholder: 'Please enter task name'
    }
  }, {
    label: 'Execution cycle',
    group: [{
      type: 'select',
      name: 'type',
      value: 'week',
      list: [
        { title: 'Daily', value: 'day' },
        { title: 'N Days', value: 'day-n' },
        { title: 'Hourly', value: 'hour' },
        { title: 'N Hours', value: 'hour-n' },
        { title: 'N Minutes', value: 'minute-n' },
        { title: 'Weekly', value: 'week' },
        { title: 'Monthly', value: 'month' }
      ],
      change: function (formData, element, that) {
        crontab.crontabType(that.config.form, formData)
        that.$replace_render_content(2)
      }
    }, {
      type: 'select',
      name: 'week',
      value: '1',
      list: [
        { title: 'Monday', value: '1' },
        { title: 'Tuesday', value: '2' },
        { title: 'Wednesday', value: '3' },
        { title: 'Thursday', value: '4' },
        { title: 'Friday', value: '5' },
        { title: 'Saturday', value: '6' },
        { title: 'Sunday', value: '0' }
      ]
    }, {
      type: 'number',
      display: false,
      name: 'where1',
      'class': 'group',
      width: '70px',
      value: '3',
      unit: 'Day',
      // min: 1,
      // max: 31
    }, {
      type: 'number',
      name: 'hour',
      'class': 'group',
      width: '70px',
      value: '1',
      unit: 'Hour',
      // min: 0,
      // max: 23
    }, {
      type: 'number',
      name: 'minute',
      'class': 'group',
      width: '70px',
      // min: 0,
      // max: 59,
      value: '30',
      unit: 'Minute'
    }]
  }, {
    label: 'Backup Site',
    display: false,
    group: [{
      type: 'select',
      name: 'sName',
      width: '150px',
      placeholder: 'no site data',
      list: siteListAll,
      change: function (formData, element, that) {
        var nameForm = that.config.form[1]
        if (formData.sType === 'enterpriseBackup') {
            crontab.getAllTables(formData.datab_name,function(res) {
            that.config.form[3].group[3].list = res
            that.config.form[3].group[3].display = formData.sName === 'tables'
            that.$replace_render_content(3)
            var select_data = (formData.sName === 'databases' ? formData.datab_name : (formData.datab_name+'---'+ res[0].value))
            nameForm.group.value = '[Do not delete] database incremental backup[ ' + (formData.sName === 'databases' ? formData.datab_name : (formData.datab_name+'---'+ res[0].value)) + ' ]'
            if(!formData.datab_name) nameForm.group.value = '[Do not delete] database incremental backup'
            that.$local_refresh('name', nameForm.group)
          })
        }else{
          nameForm.group.value = crontab.typeTips[formData.sType] + '[ ' + (formData.sName === 'ALL' ? 'ALL' : formData.sName) + ' ]'
        }
        that.$local_refresh('name', nameForm.group)
      }
    }, {
      type: 'text',
      width: '200px',
      name: 'path',
      display: false,
      icon: {
        type: 'glyphicon-folder-open',
        event: function (formData, element, that) {
          $("#bt_select").one('click', function () {
            that.config.form[1].group.value = 'Backup Directory[' + element['path'].val() + ']'
            that.$local_refresh('name', that.config.form[1].group)
          })
        }
      },
      value: bt.get_cookie('sites_path') ? bt.get_cookie('sites_path') : '/www/wwwroot',
      placeholder: 'Please select directory'
    },{
      label: 'Database',
      display: false,
      type: 'select',
      name: 'datab_name',
      width: '150px',
      list: allDatabases,
      change: function (formData, element, that) {
        var nameForm = that.config.form[1]
        crontab.getAllTables(formData.datab_name,function (res) {
          that.config.form[3].group[3].list = res
          that.$replace_render_content(3)
          var select_data = (formData.sName === 'databases' ? formData.datab_name : formData.datab_name+'---'+res[0].value)
           nameForm.group.value = '[Do not delete] database incremental backup[ ' + (formData.sName === 'databases' ? formData.datab_name : formData.datab_name+'---'+res[0].value) + ' ]'
          if(!select_data){nameForm.group.value = '[Do not delete] database incremental backup'}
          that.$local_refresh('name', nameForm.group)
        })
      }
    },{
      type: 'select',
      display: false,
      label: 'Tables',
      name: 'tables_name',
      width: '150px',
      list: allTables,
      change: function (formData, element, that) {
        var nameForm = that.config.form[1]
        if (formData.sType === 'enterpriseBackup') {
            var select_data = (formData.sName === 'databases' ? formData.datab_name : formData.datab_name+'---'+formData.tables_name)
            nameForm.group.value = '[Do not delete] database incremental backup[ ' + (formData.sName === 'databases' ? formData.datab_name : formData.datab_name+'---'+formData.tables_name) + ' ]'
            if(!select_data) { nameForm.group.value = '[Do not delete] database incremental backup'}
        }
        that.$local_refresh('name', nameForm.group)
      }
    } ,{
      type: 'select',
      name: 'backupTo',
      label: 'Backup to ',
      width: '150px',
      placeholder: 'No stored information',
      value: 'localhost',
      list: backupListAll,
      change: function (formData, element, that) {
        if (that.data.sType!=='enterpriseBackup' && formData.sType !== 'enterpriseBackup') {
          that.config.form[3].group[4].value = formData.backupTo;
          that.config.form[3].group[5].value = formData.save;
          that.config.form[3].group[6].display = formData.backupTo !== "localhost" ? true : false;
          switch(formData.sType){
            case 'site':
            case 'database':
              that.config.form[3].group[0].value = formData.sName
              break;
            case 'path':
              that.config.form[3].group[1].value = formData.path
              break;
          }
          that.$replace_render_content(3)
        }
      }
    }, {
      label: 'Keep last',
      type: 'number',
      name: 'save',
      'class': 'group',
      width: '70px',
      value: '3',
      unit: 'copies'

    }, {
      type: 'checkbox',
      name: 'save_local',
      display: false,
      style: { "margin-top": "7px" },
      value: 1,
      title: 'Keep local backup',
      event: function (formData, element, that) {
        that.config.form[3].group[6].value = !formData.save_local ? '0' : '1';
      }
    }]
  }, {
    label: 'Error notify',
    display: false,
    group: [{
      type: 'select',
      name: 'notice',
      value: 0,
      list: [
        { title: 'No notice', value: 0 },
        { title: 'Notify on failure', value: 1 }
      ],
      change: function (formData, element, that) {
        var notice_channel_form = that.config.form[4], notice = parseInt(formData.notice)
        notice_channel_form.group[1].display = !!notice
        notice_channel_form.group[0].value = notice
        that.$replace_render_content(4)

        var flag = false;
        if (formData.notice !== '0') {
          flag = that.config.form[4].group[1].list.length == 0;
        }
        that.config.form[8].group.disabled = flag;
        that.$local_refresh('submitForm', that.config.form[8].group);
      }
    }, {
      label: 'Notification',
      type: 'select',
      name: 'notice_channel',
      display: false,
      width: '100px',
      placeholder: 'No config notification',
      list: {
        url: '/config?action=get_msg_configs',
        dataFilter: function (res, that) {
          return crontab.pushChannelMessage.getChannelSwitch(res,that.config.form[0].group.value)
        },
        success: function (res, that, config, list) {
          if(!config.group[1].value && config.group[0].value == 1){
            config.group[1].value = list.length > 0 ? list[0].value : []
          }
          if (list.length === 0) {
            that.config.form[8].group.disabled = true
            that.$local_refresh('submitForm', that.config.form[8].group)
          }
        }
      }
    }, {
      type: 'link',
      'class': 'mr5',
      title: 'Set Notification',
      event: function (formData, element, that) {
        open_three_channel_auth();
      }
    }]
  }, {
    label: 'Script content',
    group: {
      type: 'textarea',
      name: 'sBody',
      style: {
        'width': '500px',
        'min-width': '500px',
        'min-height': '130px',
        'line-height': '22px',
        'padding-top': '10px',
        'resize': 'both'
      },
      placeholder: 'Please enter script content'
    }
  }, {
    label: 'URL address',
    display: false,
    group: {
      type: 'text',
      width: '500px',
      name: 'urladdress',
      value: 'http://',
      event: function (formData, element, that) {
        if (formData.sType === 'enterpriseBackup') {
          $('.glyphicon-repeat').on('click',function(){
            that.config.form[6].group.value = bt.get_random(bt.get_random_num(6,10))
            that.$local_refresh('urladdress', that.config.form[6].group)
            $('input[name=urladdress]').click()
          })
        }
      }
    }
  }, {
    label: 'Tips',
    display: false,
    group: {
      type: 'help',
      name: 'webshellTips',
      style: { 'margin-top': '6px' },
      list: ['Free RAM of PHP/MySQL/Pure-FTPd/Apache/Nginx, recommended to be executed every midnight!']
    }
  }, {
    label: '',
    group: {
      type: 'button',
      size: '',
      name: 'submitForm',
      title: 'Add task',
      event: function (formData, element, that) {
        formData['save_local'] = that.config.form[3].group[6].value.toString();
        that.submit(formData)
      }
    }
  }],
  /**
   * @description 计划任务类型解构调整
   * @param {}
   * @param {}
   * @param {Add} 是否是添加
   */

  crontabsType: function (config, formData, Add) {
	config[4].group[1].name = 'notice_channel';
	config[3].group[4].list = backupListAll;
	// config[2].group[0].value = 'week';
	switch (formData.sType) {
		case 'toShell':
			break;
		case 'enterpriseBackup':
			config[2].label = 'Backup cycle'
			config[2].group[0].display = false
			config[2].group[1].display = false
			config[2].group[2].display = false
			config[2].group[3].display = true
			config[2].group[4].display = false
			config[6].display = false;
			config[3].group[0].list = [{title: 'Database', value: 'databases'},{title: 'Table', value: 'tables'}];
			config[3].label = 'Backup type'
			config[3].group[0].placeholder = ''
			config[3].group[4].placeholder = ''
			config[3].group[4].value = ['localhost']
			config[3].group[4].width = '300px'
			config[3].group[2].list = allDatabases
			config[3].group[4].list = backuptolist
			config[3].group[4].type = 'multipleSelect'
			config[3].group[2].display = true;
			config[3].group[5].display = false;
			config[3].display = true;
			config[6].display = true;
			config[6].label = 'Compression password'
			config[6].group.width = '250px'
			config[6].group.unit = '<span class="glyphicon glyphicon-repeat cursor mr5"></span><span style="margin-left:5px;color:red;">Note: Please record the compression password, if the compression password is lost, the data cannot be recovered and download</span>'
			config[6].group.placeholder = 'Please enter the compression password, which can be empty'
			config[6].group.value = ''
			config[1].group.disabled = true // 禁用任务名称，不允许修改
			config[5].display = false;
			config[4].display = true;
			config[7].display = true;
			config[7].group.list = ''
			config[7].group.unit = '<span class="alertMsg">Tips: 1. The current database does not support SQLServer, MongoDB, Redis, PgSQL backup<br/><span>2. Note: Incremental backup temporarily fixes the default backup directory to be: /www/backup</span></span>'
			if (Add) {
				config[2].group[0].value = 'hour-n'
				config[2].group[3].value = '3'
			}
			if(bt.get_cookie('ltd_end')<0){
					config[2].group[3].disabled = true
					config[3].group[0].disabled = true
					config[3].group[2].display = false
					config[3].group[4].disabled = true
					config[4].group[0].disabled = true
					config[6].group.disabled = true
					config[8].group.title = 'Upgrade the professional version to use'
			}
			break;
		case 'database':
			config[3].group[0].placeholder = 'No database data';
			config[5].display = false;
			config[7].display = true;
			config[7].group.list = ''
			config[7].group.unit = '<span class="alertMsg">The current database does not support SQLServer, MongoDB, Redis, PgSQL backup</span>'
			if (Add) {
				config[2].group[0].value = 'day'
				config[2].group[1].display = false
				config[2].group[3].value = '2'
				config[2].group[4].value = '30'
			}
		case 'logs':
			if (formData.sType === 'logs') {
				if(Add){
					config[2].group[3].value = '0'
					config[2].group[4].value = '1'
					config[2].group[0].value = 'day'
				}
				config[2].group[1].display = false
				config[3].group[4].display = false
				config[3].group[5].value = 180
			}
		case 'path':
			if (formData.sType === 'path') {
				config[1].group.value = 'Backup Directory[' + config[3].group[1].value + ']'
				if(Add) {
					config[2].group[0].value = 'day'
					config[2].group[1].display = false
				}
				config[3].group[0].display = false
				config[3].group[1].display = true
				config[3].group[4].list = backupListAll
			}
		case 'webshell':
			if (formData.sType === 'webshell') {
				config[3].group[0].unit = '<span style="margin-top: 9px; display: inline-block;">*本次查杀由长亭牧云强力驱动</span>';
				config[3].group[4].display = false
				config[3].group[5].display = false
				config[3].group[6].display = false
				config[4].display = true
				config[4].label = '消息通道'
				config[4].group[1].name = 'urladdress'
				config[4].group[0].display = false
				delete config[4].group[1].label
				config[4].group[1].display = true
				config[5].display = false
			}
		case 'site':
			config[3].group[0].list = siteListAll;
			config[3].label = crontab.typeTips[formData.sType]
			if (formData.sType !== 'path') config[1].group.disabled = true // 禁用任务名称，不允许修改
			config[3].display = true // 显示备份网站操作模块
			if (formData.sType === 'database' || formData.sType === 'site' || formData.sType === 'path') config[4].display = true
			config[5].label = 'Exclusion rule'
			config[5].group.placeholder = 'For each rule in a row, the directory cannot end with /, e.g.\ndata/config.php\nstatic/upload\n *.log\n'
			break;
		case 'syncTime':
			config[1].group.value = 'Synchronize server time periodically'
			config[5].group.value = 'which ntpdate > /dev/null\n' +
			'if [ $? = 1 ];then\n' +
			'\tif [ -f "/etc/redhat-release" ];then\n' +
			'\t\tyum install -y ntpdate\n' +
			'\telse\n' +
			'\t\tapt-get install -y ntpdate\n' +
			'\tfi\n' +
			'fi\n' +
			'echo "|-Trying to get from 1.pool.ntp.org Sync time..";\n' +
			'ntpdate -u 1.pool.ntp.org\n' +
			'if [ $? = 1 ];then\n' +
			'\techo "|-Trying to get from 0.pool.ntp.org Sync time..";\n' +
			'\tntpdate -u 0.pool.ntp.org\n' +
			'fi\n' +
			'if [ $? = 1 ];then\n' +
			'\techo "|-Trying to get from 2.pool.ntp.org Sync time..";\n' +
			'\tntpdate -u 2.pool.ntp.org\n' +
			'fi\n' +
			'if [ $? = 1 ];then\n' +
			'\techo "|-Trying to get from time.cloudflare.com Sync time..";\n' +
			'\tntpdate -u time.cloudflare.com\n' +
			'fi\n' +
			'echo "|-Trying to write current system time to hardware..";\n' +
			'hwclock -w\n' +
			'date\n' +
			'echo "|-Time synchronization complete!";'
			break;
		case 'rememory':
			config[1].group.value = 'Free RAM'
			config[5].display = false
			config[7].display = true
			break;
		case 'toUrl':
			config[5].display = false
			config[6].display = true
			break;
	}
	if (formData.sType === 'database') config[3].group[0].list = databaseListAll;
	if (Add && (formData.sType === 'database' || formData.sType === 'logs' || formData.sType === 'site')) {
		config[3].group[0].value = 'ALL';
	}
	config[0].group.value = formData.sType
	return config
},

  /**
   * @description 计划任务类型解构调整
   */
  crontabType: function (config, formData) {
    var formConfig = config[2];
    switch (formData.type) {
      case 'day-n':
      case 'month':
      case 'day':
        formConfig.group[1].display = false
        $.extend(formConfig.group[2], {
          display: formData.type !== 'day',
          unit: formData.type === 'day-n' ? 'Day' : 'Day'
        })
        formConfig.group[3].display = true
        break;
      case 'hour-n':
      case 'hour':
      case 'minute-n':
        formConfig.group[1].display = false
        formConfig.group[2].display = false
        formConfig.group[3].display = formData.type === 'hour-n'
        formConfig.group[4].value = formData.type === 'minute-n' ? 3 : 30
        break;
      case 'week':
        formConfig.group[1].display = true
        formConfig.group[2].display = false
        formConfig.group[3].display = true
        break;

    }
    var num = formData.sType == 'logs' ? 0 : 1;
    var hour = formData.hour ? formData.hour : num;
    var minute = formData.minute ? formData.minute : 30;
    formConfig.group[3].value = parseInt(hour).toString();
    formConfig.group[4].value = parseInt(minute).toString()
    formConfig.group[0].value = formData.type;
    return config;
  },
  /**
   * @description 添加计划任务表单
   */
  addCrontabForm: function () {
    var _that = this
    return bt_tools.form({
      el: '#crontabForm',
      'class': 'crontab_form',
      form: arryCopy(crontab.crontabFormConfig),
      submit: function (formData) {
        var form = $.extend(true, {}, _that.crontabForm), _where1 = $('input[name=where1]'), _hour = $('input[name=hour]'), _minute = $('input[name=minute]');
        $.extend(form, formData)
        if (form.name === '') {
          bt.msg({ status: false, msg: 'Task name cannot be empty!' })
          return false
        }
        if (_where1.length > 0) {
          if (_where1.val() > 31 || _where1.val() < 1 || _where1.val() == '') {
            _where1.focus();
            layer.msg('Please enter the correct cycle range [1-31]', { icon: 2 });
            return false;
          }
        }
        if (_hour.length > 0) {
          if (_hour.val() > 23 || _hour.val() < 0 || _hour.val() == '') {
            _hour.focus();
            layer.msg('Please enter the correct cycle range [0-23]', { icon: 2 });
            return false;
          }
        }
        if (_minute.length > 0) {
          if (_minute.val() > 59 || _minute.val() < 0 || _minute.val() == '') {
            _minute.focus();
            layer.msg('Please enter the correct cycle range [0-59]', { icon: 2 });
            return false;
          }
        }
        switch (form.type) {
          case "minute-n":
            form.where1 = form.minute;
            form.minute = '';
            if(form.where1 < 1) return bt.msg({ status: false, msg: 'Minute cannot be less than 1！' })
            break;
          case "hour-n":
            form.where1 = form.hour;
            form.hour = '';
            if(form.minute <= 0 && form.where1 <= 0) return bt.msg({ status: false, msg: 'Hour and minute cannot be less than 1 at the same time!' })
            break;
            // 天/日默认最小为1
        }
        switch (form.sType) {
          case 'syncTime':
            if (form.sType === 'syncTime') form.sType = 'toShell'
          case 'toShell':
            if (form.sBody === '') {
              bt.msg({ status: false, msg: 'Script content cannot be empty!' })
              return false
            }
            break;
          case 'path':
            form.sName = form.path
            delete form.path
            if (form.sName === '') {
              bt.msg({ status: false, msg: 'Backup directory cannot be empty!' })
              return false
            }
            break;
          case 'toUrl':
            if (!bt.check_url(form.urladdress)) {
              layer.msg(lan.crontab.input_url_err, { icon: 2 });
              $('#crontabForm input[name=urladdress]').focus();
              return false;
            }
            break;
          case 'enterpriseBackup':
            if (form.hour < 1) {
              layer.msg('The backup cycle should be greater than 0', { icon: 2 });
              $('#crontabForm input[name=hour]').focus();
              return false;
            }
            break;
        }
        if (form.sType == "site" || form.sType == "database" || form.sType == "path" || form.sType == "logs") {
          if (Number(form.save) < 1 || form.save == '') {
            return bt.msg({status: false, msg: 'Keep latest cannot be less than 1!'});
          }
        }
        var url = '/crontab?action=AddCrontab',params = form
        if (form.sType == "enterpriseBackup") {
          var multipleValues = $('select[name=backupTo]').val()
          if(multipleValues == null) return layer.msg('Please select at least one backup type')
          url = 'project/binlog/add_mysqlbinlog_backup_setting'
          params = {
            datab_name : form.datab_name,
            backup_type : form.sName,
            zip_password : form.urladdress,
            cron_type : 'hour-n',
            backup_cycle : form.hour,
            upload_localhost : multipleValues.indexOf('localhost') > -1 ? 'localhost' : '',
            upload_alioss : multipleValues.indexOf('alioss') > -1 ? 'alioss' : '',
            upload_txcos : multipleValues.indexOf('txcos') > -1 ? 'txcos' : '',
            upload_qiniu : multipleValues.indexOf('qiniu') > -1 ? 'qiniu' : '',
            upload_obs : multipleValues.indexOf('obs') > -1 ? 'obs' : '',
            upload_bos : multipleValues.indexOf('bos') > -1 ? 'bos' : '',
            notice : form.notice,
            notice_channel : form.notice_channel,
          }
          if(params.backup_type == 'tables') {
            params['table_name'] = form.tables_name
            if(form.tables_name == '') return layer.msg("There is no table in the current database and cannot be added")
          }
        }
         if(bt.get_cookie('ltd_end') < 0 && form.sType === 'enterpriseBackup'){
                 $.post("plugin?action=get_soft_find", {
                    sName: 'enterprise_backup'
                  }, function (rdata) {
                    rdata.description = ['快速恢复数据','支持数据安全保护','支持增量备份','支持差异备份']
                    rdata.pluginName = '企业增量备份'
                    rdata.ps = '指定数据库或指定表增量备份，支持InnoDB和MyISAM两种存储引擎，可增量备份至服务器磁盘、阿里云OSS、腾讯云COS、七牛云存储、华为云存储、百度云存储'
                    rdata.imgSrc='https://www.bt.cn/Public/new/plugin/introduce/database/backup.png'
                    product_recommend.recommend_product_view(rdata,{imgArea: ['890px', '620px']},'ltd',53,'ltd')
                 })
                  return
            }else{
        bt_tools.send({
          url: url,
          data: params
        }, function (res) {
          _that.addCrontabForm.data = {}
          _that.addCrontabForm.$again_render_form(_that.crontabFormConfig)
          _that.crontabTabel.$refresh_table_list(true)
          bt_tools.msg(res)
        }, 'Add Cron Job');
      }

      }
    })
  },
  /**
   * @description 获取所有数据库名
   */
  getAllDatabases: function (callback){
    $.post('project/binlog/get_databases', function (res) {
      allDatabases = []
      if (res.length == 0) {
        allDatabases = [{title:'Current no database',value:''}]
      }else{
        for (let i = 0; i < res.length; i++) {
          allDatabases.push({title:res[i].name,value:res[i].name})
        }
      }
      if (callback) callback(res)
    })
  },
  /**
   * @description 取指定数据库的所有表名
   * @param {object} param 参数对象
   * @param {function} callback 回调函数
   */
  getAllTables: function (param, callback) {
    $.post('project/binlog/get_tables', {db_name: param} , function (res) {
      var data = [],allTables = []
      for (let i = 0; i < res.length; i++) {
        data.push({title:res[i].name,value:res[i].name})
      }
      if (data.length == 0) {
        allTables = [{title:'Current database has no tables',value:''}]
      }else{
        allTables = data
      }
      if (callback) callback(allTables)
    })
  },
  /**
   * @description 获取计划任务存储列表
   * @param {function} callback 回调函数
   */
  getDataList: function (type, callback) {
    if ($.type(type) === 'function') callback = type, type = 'sites'
    bt_tools.send({
      url: '/crontab?action=GetDataList',
      data: { type: type }
    }, function (res) {
      var backupList = [{ title: 'Local disk', value: 'localhost' }];
      for (var i = 0; i < res.orderOpt.length; i++) {
        var item = res.orderOpt[i]
        backupList.push({ title: item.name, value: item.value })
      }
      backupListAll = backupList
      var siteList = [{ title: 'ALL', value: 'ALL' }];
      for (var i = 0; i < res.data.length; i++) {
        var item = res.data[i]
        siteList.push({ title: item.name + ' [ ' + item.ps + ' ]', value: item.name });
      }
      if (siteList.length === 1) siteList = []
      if (type === 'sites') {
        siteListAll = siteList
      } else {
        databaseListAll = siteList
      }
      if (callback) callback(res)
    }, 'Getting storage configuration');
  },
  /**
   * @description 删除计划任务
   * @param {object} param 参数对象
   * @param {function} callback 回调函数
   */
  delCrontab: function (param, callback) {
    bt_tools.send({
      url: '/crontab?action=DelCrontab',
      data: { id: param.id }
    }, function (res) {
      bt.msg(res)
      if (res.status && callback) callback(res)
    }, 'Delete cron task');
  },
  /**
   * @description 执行计划任务
   * @param {object} param 参数对象
   * @param {function} callback 回调函数
   */
  startCrontabTask: function (param, callback) {
    bt_tools.send({
      url: '/crontab?action=StartTask',
      data: { id: param.id }
    }, function (res) {
      bt.msg(res)
      if (res.status && callback) callback(res)
    }, 'Execute cron task');
  },
  /**
   * @description 获取计划任务执行日志
   * @param {object} param 参数对象
   * @param {function} callback 回调函数
   */
  getCrontabLogs: function (param, callback) {
    bt_tools.send({
      url: '/crontab?action=GetLogs',
      data: { id: param.id }
    }, function (res) {
      if (res.status) {
        if (callback) callback(res)
      } else {
        bt.msg(res)
      }
    }, 'Getting execute log');
  },
  /**
   * @description 获取计划任务执行日志
   * @param {object} param 参数对象
   * @param {function} callback 回调函数
   */
  clearCrontabLogs: function (param, callback) {
    bt_tools.send({
      url: '/crontab?action=DelLogs',
      data: { id: param.id }
    }, function (res) {
      bt.msg(res)
      if (res.status && callback) callback(res)
    }, 'clear execute log');
  },
  /**
   * @description 获取计划任务执行状态
   * @param {object} param 参数对象
   * @param {function} callback 回调函数
   */
  setCrontabStatus: function (param, callback) {
    bt_tools.send({
      url: '/crontab?action=set_cron_status',
      data: { id: param.id }
    }, function (res) {
      bt.msg(res)
      if (res.status && callback) callback(res)
    }, 'Set task status');
  },
  /**
   * @description 计划任务表格
   */
  crontabTabel: function () {
    var _that = this
    return bt_tools.table({
      el: '#crontabTabel',
      url: '/crontab?action=GetCrontab',
      minWidth: '1000px',
      autoHeight: true,
      'default': "Cron task list is empty", //数据为空时的默认提示
      height: 300,
      dataFilter: function (res) {
        return { data: res };
      },
      column: [
        { type: 'checkbox', 'class': '', width: 20 },
        {
          fid: 'name',
          title: "Tasks Name"
        },
        {
          fid: 'status',
          title: "Status",
          width: 80,
          config: {
            icon: true,
            list: [
              [1, 'Normal', 'bt_success', 'glyphicon-play'],
              [0, 'Disable', 'bt_danger', 'glyphicon-pause']
            ]
          },
          type: 'status',
          event: function (row, index, ev, key, that) {
            bt.confirm({
              title: 'Set task status',
              msg: parseInt(row.status) ? 'The cron job will not continue to run after suspended. Are you sure to suspend this cron job?' : 'The cron job deactivated, are sure to enable this cron job?'
            }, function () {
              _that.setCrontabStatus(row, function () {
                that.$refresh_table_list(true)
              })
            })
          }
        },
        // {
        //   fid: 'type',
        //   title: "周期",
        //   width: 120
        // },
        {
          fid: 'cycle',
          title: "Time of Executing\t",
          template: function (row, index) {
            if (row.sType == "enterpriseBackup") {
              return '<span>Execute every '+row.where1+' hours</span>'
            }
            return '<span>'+ row.cycle +'</span>'
          }
        },
          //aapanel部分插件还没有更新导致上传到插件存储的无法查看保存数量先注释
        //   {
        //   fid: 'save',
        //   title: "Save number",
        //   template: function (row) {
        //     if(typeof row.sBody == 'undefined' || row.sBody == null) return '<span>' + (row.save > 0 ? +row.save + ' copies' : '-') + '</span>'
		// 				if(row.sType == 'enterpriseBackup' || row.sType == 'logs'|| row.sBody.indexOf('run_log_split.py') !=-1) return '<span>' + (row.save > 0 ? +row.save + ' copies' : '-') + '</span>'
		// 				return '<div><span>' + (row.save > 0 ? +row.save + ' copies' : '-') + '</span><span class="btlink crontab_show_backup" data-id="'+ row.id+'" data-name="'+row.name +'"> '+(row.save > 0 ? '[View]' : '')+'</span></div>'
        //   }
        // },
          {
          fid: 'backupTo',
          title: "Backup to",
          width: 170,
          template: function (row, index) {
            if (row.sType == "enterpriseBackup") {
              var arry = [],arry1 = []
              arry = row.backupTo.split("|")
              for (var i = 0; i < arry.length; i++) {
                for (var j = 0; j < backuptolist.length; j++) {
                  if (arry[i] == backuptolist[j].value) {
                    arry1.push(backuptolist[j].title)
                  }
                }
              }
              return '<span>' + arry1 + '</span>'
            } else {
              for (var i = 0; i < backupListAll.length; i++) {
                var item = backupListAll[i]
                if (item.value === row.backupTo) {
                  if (row.sType === 'toShell') return '<span>--</span>';
                  return '<span>' + item.title + '</span>'
                }
              }
              return '<span>--</span>'
            }
          }
        }, {
          fid: 'addtime',
          title: 'Last execution time',
        },
        {
          title: "Operation",

          type: 'group',
          align: 'right',
          group: [{
            title: 'Execute',
            event: function (row, index, ev, key, that) {
              _that.startCrontabTask(row, function (res) {
                that.$refresh_table_list(true);
                if(res.status) {
                  setTimeout(function () {
                    layer.closeAll()
                    $('#crontabTabel .table tbody tr:eq('+ index +')').find('[title="Log"]').click()
                  }, 1000)
                }
              })
            }
          }, {
            title: 'Edit',
            event: function (row, index, ev, key, that) {
              var arry = [],db_result,t_result
              arry = row.urladdress.split("|")
              if(row.sType === 'enterpriseBackup'){
                crontab.getAllDatabases(function (rdata) {
                  crontab.getAllTables(arry[0],function(res) {
                    db_result = rdata.some(function(item){
                      if (item.name === arry[0]) {
                        return true
                      }
                    })
                    if(arry[1] !== ''){
                      t_result = res.some(function(item){
                        if (item.value === arry[1]) {
                          return true
                        }
                      })
                    }
                    edit(res)
                  })
                })
              }else{
                edit()
              }
              function edit(table_list) {
                layer.open({
                  type: 1,
                  title: 'Edit Cron task -[' + row.name + ']',
                  area: row.sType != "enterpriseBackup" ? '990px':'1140px',
                  skin: 'layer-create-content',
                  shadeClose: false,
                  closeBtn: 2,
                  content: '<div class="ptb20" id="editCrontabForm" style="min-height: 400px"></div>',
                  success: function (layers, indexs) {
                    bt_tools.send({
                      url: '/crontab?action=get_crond_find',
                      data: { id: row.id }
                    }, function (rdata) {
                      var formConfig = arryCopy(crontab.crontabFormConfig),
                          form = $.extend(true, {}, _that.crontabForm),
                          cycle = {};
                      for (var keys in form) {
                        if (form.hasOwnProperty.call(form, keys)) {
                          form[keys] = typeof rdata[keys] === "undefined" ? '' : rdata[keys]
                        }
                      }
                      crontab.crontabType(formConfig, form)
                      crontab.crontabsType(formConfig, form)
                      switch (rdata.type) {
                        case 'day':
                          cycle = { where1: '', hour: rdata.where_hour, minute: rdata.where_minute }
                          break;
                        case 'day-n':
                          cycle = { where1: rdata.where1, hour: rdata.where_hour, minute: rdata.where_minute }
                          break;
                        case 'hour':
                          cycle = { where1: rdata.where1, hour: rdata.where_hour, minute: rdata.where_minute }
                          break;
                        case 'hour-n':
                          cycle = { where1: rdata.where1, hour: rdata.where1, minute: rdata.where_minute }
                          break;
                        case 'minute-n':
                          cycle = { where1: rdata.where1, hour: '', minute: rdata.where1 }
                          break;
                        case 'week':
                          formConfig[2].group[1].value = rdata.where1
                          cycle = { where1: '', week: rdata.where1, hour: rdata.where_hour, minute: rdata.where_minute }
                          break;
                        case 'month':
                          cycle = { where1: rdata.where1, where: '', hour: rdata.where_hour, minute: rdata.where_minute }
                          break;
                      }

                      if (rdata.sType !== 'enterpriseBackup') {
                        formConfig[3].group[4].value = rdata.backupTo;
                        formConfig[3].group[6].display = (rdata.backupTo != "" && rdata.backupTo != 'localhost');
                        formConfig[3].group[6].value = rdata.save_local;
                      }
                      formConfig[4].group[0].value = rdata.notice;
                      formConfig[4].group[1].display = rdata.sType == 'webshell' ? true : !!rdata.notice;    //单独判断是否为木马查杀
                      if (formConfig[4].group[1].display) {
                        formConfig[4].group[1].display = true;
                        formConfig[4].group[1].value = (rdata.sType == 'webshell' ? rdata.urladdress : (rdata.notice_channel === '' ? first : rdata.notice_channel))
                      }
                      $.extend(form, cycle, { id: rdata.id })



                      switch (rdata.sType) {
                        case 'logs':
                        case 'path':
                          form.path = rdata.sName
                          formConfig[3].group[1].disabled = true
                          break
                        case 'enterpriseBackup':
                          formConfig[3].group[2].value = arry[0]
                          formConfig[3].group[2].disabled = true
                          if(arry[1] !== ''){
                            // formConfig[3].group[3].list = [{title:arry[1],value:arry[1]}]
                            formConfig[3].group[3].list = table_list
                            formConfig[3].group[3].value = arry[1]
                            formConfig[3].group[3].disabled = true
                            formConfig[3].group[3].display = true
                          }
                          if (!t_result) {
                            formConfig[3].group[3].placeholder = 'Table does not exist'
                            var none_db = formConfig[3].group[3].list.some(function(item){
                              if (item.value === '') {
                                return true
                              }
                            })
                            if (none_db) formConfig[3].group[3].list = []
                          }
                          if (!db_result) {
                            formConfig[3].group[2].placeholder = 'Database does not exist'
                            formConfig[3].group[3].placeholder = 'Table does not exist'
                            formConfig[3].group[3].list = []
                          }
                          formConfig[3].group[1].disabled = true
                          formConfig[6].display = false
                          var backT = rdata.backupTo.split('|'), backupTolist = []
                          for (var i = 0; i < backT.length; i++) {
                            if (backT[i] != '') {
                              backupTolist.push(backT[i])
                            }
                          }
                          formConfig[3].group[4].value = backupTolist
                          break;
                        case 'toShell':
                            if(rdata.save){
                              formConfig[2].group[0].disabled = true
                              if(rdata.type === 'minute-n'){
                                formConfig[2].group[4].disabled = true
                              }
                              formConfig[3].group[5].value = rdata.save
                              for (var i = 0; i < formConfig[3].group.length; i++) {
                                if(i === 5) {
                                  delete formConfig[3].group[i]['label']
                                  formConfig[3].group[i].display = true
                                }else{
                                  formConfig[3].group[i].display = false
                                }
                              }
                              formConfig[3].label = 'Keep last'
                              formConfig[3].display = true
                            }
                            break;
                      }
                      formConfig[0].group.disabled = true
                      formConfig[1].group.disabled = true
                      formConfig[3].group[0].disabled = true
                      formConfig[8].group.title = 'Save'
                      var screen = ['site','database','logs','path','webshell']
                      if(screen.indexOf(form.sType) > -1){
                        if (form.sName === 'ALL') {
                          form.name = form.name.replace(/\[(.*)]/, '[ ALL ]');
                        } else {
                          form.name = form.name.replace(/\[(.*)]/, '[ ' + form.sName + ' ]');
                        }
                      }

                      delete formConfig[0].group.unit

                      bt_tools.form({
                        el: '#editCrontabForm',
                        'class': 'crontab_form',
                        form: formConfig,
                        data: form,
                        submit: function (formData) {
                          var submitForm = $.extend(true, {}, _that.crontabForm, formData, {
                            id: rdata.id,
                            sType: rdata.sType
                          })
                          if (submitForm.name === '') {
                            bt.msg({ status: false, msg: 'Task name cannot be empty!' })
                            return false
                          }
                          switch (submitForm.sType) {
                            case 'syncTime':
                              if (submitForm.sType === 'syncTime') submitForm.sType = 'toShell'
                            case 'toShell':
                              if (submitForm.sBody === '') {
                                bt.msg({ status: false, msg: 'Script content cannot be empty!' })
                                return false
                              }
                              if(rdata.save !== ''){
                                submitForm.type = rdata.type
                              }
                              break;
                            case 'path':
                              submitForm.sName = submitForm.path
                              delete submitForm.path
                              if (submitForm.sName === '') {
                                bt.msg({ status: false, msg: 'Backup directory cannot be empty!' })
                                return false
                              }
                              break;
                            case 'toUrl':
                              if (!bt.check_url(submitForm.urladdress)) {
                                layer.msg(lan.crontab.input_url_err, { icon: 2 });
                                $('#editCrontabForm input[name=urladdress]').focus();
                                return false;
                              }
                              break;
                            case 'enterpriseBackup':
                              if (submitForm.hour == '')  return bt.msg({ status: false, msg: 'Backup cycle cannot be empty!' })
                              if (submitForm.hour < 0)  return
                              break;
                          }

                          var hour = parseInt(submitForm.hour), minute = parseInt(submitForm.minute), where1 = parseInt(submitForm.where1)

                          switch (submitForm.type) {
                            case 'hour':
                            case 'minute-n':
                              if (minute < 0 || minute > 59 || isNaN(minute)) return bt.msg({ status: false, msg: 'Please enter the correct minute range 0-59 minutes' })
                              if (submitForm.type === 'minute-n') {
                                submitForm.where1 = submitForm.minute
                                submitForm.minute = ''
                                if(submitForm.where1 < 1) return bt.msg({ status: false, msg: 'Minute cannot be less than 1!' })
                              }
                              break;
                            case 'day-n':
                            case 'month':
                              if (where1 < 1 || where1 > 31 || isNaN(where1)) return bt.msg({ status: false, msg: 'Please enter the correct number of days 1-31 days' })
                            case 'week':
                            case 'day':
                            case 'hour-n':
                              if (hour < 0 || hour > 23 || isNaN(hour)) return bt.msg({ status: false, msg: 'Please enter the hour range 0-23 hours' })
                              if (minute < 0 || minute > 59 || isNaN(minute)) return bt.msg({ status: false, msg: 'Please enter the correct minute range 0-59 minutes' })
                              if (submitForm.type === 'hour-n') {
                                submitForm.where1 = submitForm.hour
                                submitForm.hour = ''
                                if(submitForm.minute <= 0 && submitForm.where1 <= 0) return bt.msg({ status: false, msg: 'Hour and minute cannot be less than 1 at the same time!' })
                              }
                              break;
                          }
                          if (submitForm.sType == "site" || submitForm.sType == "database" || submitForm.sType == "path" || submitForm.sType == "logs") {
                            if (Number(submitForm.save) < 1 || submitForm.save == '') {
                              return bt.msg({ status: false, msg: 'Keep latest cannot be less than 1 !'});
                            }
                          }

                          var url = '/crontab?action=modify_crond', params = submitForm
                          if (submitForm.sType == 'enterpriseBackup') {
                            var multipleValues = $('select[name=backupTo]').val()
                            if(multipleValues == null) return layer.msg('Please select at least one backup type')
                            url = 'project/binlog/modify_mysqlbinlog_backup_setting'
                            params = {
                              datab_name : arry[0],
                              cron_type : 'hour-n',
                              backup_cycle : submitForm.hour,
                              upload_localhost : multipleValues.indexOf('localhost') > -1 ? 'localhost' : '',
                              upload_alioss : multipleValues.indexOf('alioss') > -1 ? 'alioss' : '',
                              upload_txcos : multipleValues.indexOf('txcos') > -1 ? 'txcos' : '',
                              upload_qiniu : multipleValues.indexOf('qiniu') > -1 ? 'qiniu' : '',
                              upload_obs : multipleValues.indexOf('obs') > -1 ? 'obs' : '',
                              upload_bos : multipleValues.indexOf('bos') > -1 ? 'bos' : '',
                              notice : submitForm.notice,
                              notice_channel : submitForm.notice_channel,
                              cron_id : row.id,
                              backup_id : arry[2]
                            }
                            if($('select[name=datab_name]').parent().find('.bt_select_content').text().indexOf('does not exist') > -1) return layer.msg('Database['+ arry[0] +']does not exist',{icon:2})
                            if($('select[name=tables_name]').length) if($('select[name=tables_name').parent().find('.bt_select_content').text().indexOf('does not exist') > -1) return layer.msg('Table['+ arry[1] +']does not exist',{icon:2})
                          }else{
                            if($('select[name=sName]').length){
                              params.name.match(/\[(.*)]/)
                              var sName_result = formConfig[3].group[0].list.some(function(item){
                                if (item.value === (RegExp.$1.trim() === 'ALL'?'ALL':RegExp.$1.trim())) {
                                  return true
                                }
                              })
                              if(!sName_result) return layer.msg(formConfig[3].group[0].placeholder,{icon:2})
                            }
                          }
                          bt_tools.send({
                            url: url,
                            data: params
                          }, function (res) {
                            bt_tools.msg(res)
                            layer.close(indexs)
                            _that.crontabTabel.$refresh_table_list(true);
                          }, 'Edit Cron tasks')
                        }
                      })
                    }, 'Gettin configuration information')
                  }
                })
              }
            }
          }, {
            title: 'Log',
            event: function (row, index, ev, key, that) {
              var log_interval = null
              _that.getCrontabLogs(row, function (rdata) {
                layer.open({
                  type: 1,
                  title: lan.crontab.task_log_title,
                  area: ['700px', '490px'],
                  shadeClose: false,
                  closeBtn: 2,
                  content: '<div class="setchmod bt-form">\
											<pre class="crontab-log" style="overflow: auto; border: 0 none; line-height:23px;padding: 15px; margin: 0;white-space: pre-wrap; height: 405px; background-color: rgb(51,51,51);color:#f1f1f1;border-radius:0;"></pre>\
												<div class="bt-form-submit-btn" style="margin-top: 0">\
												<button type="button" class="btn btn-danger btn-sm btn-title" id="clearLogs" style="margin-right:15px;">'+ lan['public']['empty'] + '</button>\
												<button type="button" class="btn btn-success btn-sm btn-title" id="closeLogs">'+ lan['public']['close'] + '</button>\
											</div>\
										</div>',
                  success: function () {
                    var nScrollHight = 0;  //滚动距离总长(注意不是滚动条的长度)
                    var nScrollTop = 0;   //滚动到的当前位置
                    var nDivHight = $(".crontab-log").height();
                    var isDb = true
                    $(".crontab-log").scroll(function(){
                      nScrollHight = $(this)[0].scrollHeight;
                      nScrollTop = $(this)[0].scrollTop;
                      var paddingBottom = parseInt( $(this).css('padding-bottom') ),paddingTop = parseInt( $(this).css('padding-top') );
                      isDb = false
                      //判断是否滚动到底部
                      if(nScrollTop + paddingBottom + paddingTop + nDivHight >= nScrollHight){
                        isDb = true
                      }
                    });
                    var data_text = ''
                    log_interval = setInterval(function () {
                      bt_tools.send({
                        url: '/crontab?action=GetLogs',
                        data: { id: row.id }
                      }, function (res) {
                        if (res.status) {
                          var arr = res.msg.split('\n')
                          if(data_text === res.msg && arr[arr.length - 1].indexOf('-------') > -1) {
                            clearInterval(log_interval)
                            return
                          }
                          if(isDb) render_content(res)
                        }
                      })
                    }, 2000)
                    render_content(rdata)
                    function render_content(data) {
                      data_text = data.msg
                      var log_body = data.msg === '' ? 'Current log is empty' : data.msg,setchmod = $(".setchmod pre"),crontab_log = $('.crontab-log')[0]
                      setchmod.text(log_body);
                      crontab_log.scrollTop = crontab_log.scrollHeight;
                    }
                    $('#clearLogs').on('click', function () {
                      clearInterval(log_interval)
                      _that.clearCrontabLogs(row, function () {
                        $(".setchmod pre").text('')
                      })
                    })
                    $('#closeLogs').on('click', function () {
                      clearInterval(log_interval)
                      layer.closeAll()
                    })
                  },
                  cancel: function(indexs){
                    clearInterval(log_interval)
                    layer.close(indexs)
                  }
                })
              })
            }
          }, {
            title: 'Del',
            event: function (row, index, ev, key, that) {
              bt.confirm({
                title: 'Delete tasks',
                msg: 'Are you sure you want to delete the task [' + row.name + '], continue?'
              }, function () {
                if (row.sType == 'enterpriseBackup') {
                  var arry = []
                  arry = row.urladdress.split("|")
                  bt_tools.send({url: 'project/binlog/delete_mysql_binlog_setting',data: {cron_id:row.id,backup_id:arry[2],type:'cron'} },function (res) {
                    layer.msg(res.msg, {icon: res.status ? 1:2})
                    that.$refresh_table_list(true);
                  })
                }else{
                  _that.delCrontab(row, function () {
                    that.$refresh_table_list(true);
                  })
                }
              })
            }
          }]
        }
      ],
			success:function(){
				$('.crontab_show_backup').click(function(){
					var backup_id = Number($(this).data('id')),backup_name = $(this).data('name')
					var content_html = '<div style="padding:20px"><div id="backup_table_show"></div></div>'
					layer.open({
						type: 1,
						closeBtn:2,
						title:backup_name+'-backup files',
						content: content_html,
						area: ['700px', '530px'],
						success:function(){
							var backup_table = bt_tools.table({
								el: '#backup_table_show',
								url: '/crontab?action=get_backup_list',
								param: {cron_id: backup_id},
								autoHeight: true,
								default: "List is empty",
								pageName: 'backup',
								column: [
									{fid: 'name', title: 'File name',width:180,fixed:true},
									{fid: 'addtime', title: 'Backup time'},
									{fid: 'filename', title: 'Backup to',width:220,fixed:true},
									{fid: 'size', title: 'Size',template:function(row){
										return bt.format_size(row.size)
									}},
									{
										title:'OPT',
										type: 'group',
										align: 'right',
										group: [{
											title: 'Save',
											event: function (row, index, ev, key, that) {
												window.open('/download?filename=' + encodeURIComponent(row.filename));
											}
										}],
									},
								],
								tootls: [ {
									type: 'page',
									positon: ['right', 'bottom'], // 默认在右下角
									pageParam: 'p', //分页请求字段,默认为 : p
									page: 1, //当前分页 默认：1
									numberParam: 'rows',
									//分页数量请求字段默认为 : limit
									defaultNumber: 10
									//分页数量默认 : 20条
								}]
							})
						}
					})
				})
			},
      // 渲染完成
      tootls: [{ // 批量操作
        type: 'batch', //batch_btn
        positon: ['left', 'bottom'],
        placeholder: 'Please choose',
        buttonValue: 'Execute',
        disabledSelectValue: 'Please select cron task that requires batch operation!',
        selectList: [{
          title: "Execute tasks",
          url: '/crontab?action=StartTask',
          load: true,
          param: function (row) {
            return { id: row.id }
          },
          callback: function (that) { // 手动执行,data参数包含所有选中的站点
            bt.confirm({
              title: 'Batch',
              msg: 'Are you sure you want to execute the selected cron tasks in batches? Continue?'
            }, function () {
              var param = {};
              that.start_batch(param, function (list) {
                var html = '';
                for (var i = 0; i < list.length; i++) {
                  var item = list[i];
                  html += '<tr><td>' + item.name + '</td><td><div style="float:right;"><span style="color:' + (item.request.status ? '#20a53a' : 'red') + '">' + item.request.msg + '</span></div></td></tr>';
                }
                _that.crontabTabel.$batch_success_table({
                  title: 'batch execute',
                  th: 'Tasks name',
                  html: html
                });
                _that.crontabTabel.$refresh_table_list(true);
              });
            })
          }
        }, {
          title: "Delete task",
          url: function (row) {
            if (row.sType == 'enterpriseBackup') {
              var arry = []
              arry = row.urladdress.split("|")
              return 'project/binlog/delete_mysql_binlog_setting?cron_id='+row.id+'&backup_id='+arry[2]+'&type=cron'
            } else {
              return '/crontab?action=DelCrontab&id='+ row.id
            }
          },
          load: true,
          // param: function (row) {
          //   return { id: row.id }
          // },
          callback: function (that) { // 手动执行,data参数包含所有选中的站点
            bt.show_confirm("Batch delete cron tasks", "<span style='color:red'>Delete the selected cron tasks at the same time, continue?</span>", function () {
              var param = {};
              that.start_batch(param, function (list) {
                var html = '';
                for (var i = 0; i < list.length; i++) {
                  var item = list[i];
                  html += '<tr><td>' + item.name + '</td><td><div style="float:right;"><span style="color:' + (item.request.status ? '#20a53a' : 'red') + '">' + item.request.msg + '</span></div></td></tr>';
                }
                _that.crontabTabel.$batch_success_table({
                  title: 'Batch delete',
                  th: 'Tasks name',
                  html: html
                });
                _that.crontabTabel.$refresh_table_list(true);
              });
            });
          }
        }],
      }]
    })
  },
  /**
   * @descripttion 消息推送下拉
   */
  pushChannelMessage:{
    //获取通道状态
    getChannelSwitch:function(data,type) {
      var arry = [{title: 'All', value: ''}], info = [];
      for (var resKey in data) {
        if (data.hasOwnProperty(resKey)) {
          var value = resKey, item = data[resKey]
          if (!item['setup'] || $.isEmptyObject(item['data'])) continue
          info.push(value)
          arry.push({title: item.title, value: value})
        }
      }
      arry[0].value = info.join(',');
      if (type === 'webshell') arry.shift();
      if (arry.length === (type === 'webshell' ? 0 : 1)) return []
      return arry
    }
  },
  /**
   * @description 初始化
   */
  init: function () {
    var that = this;
    this.getAllDatabases()
    this.getDataList(function () {
      that.addCrontabForm = that.addCrontabForm()
			$('[title="Database incremental backup"]').html('<span style="display:flex;align-items:center">Database incremental backup<span class="new-file-icon new-ltd-icon" style="margin-left:4px"></span></span>')
      that.crontabTabel = that.crontabTabel()
      that.getDataList('databases');
    })
    function resizeTable () {
      var height = window.innerHeight - 795, table = $('#crontabTabel .divtable');
      table.css({ maxHeight: height < 400 ? '400px' : (height + 'px') })
    }
    $(window).on('resize', resizeTable)
    setTimeout(function () {
      resizeTable()
    }, 500)
  }
}
