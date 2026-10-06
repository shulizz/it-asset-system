f = r"F:\IT固定资产系统\frontend\src\views\AssetsIT.vue"
c = open(f, encoding='utf-8').read()
old = '<div class="form-row"><label>设备名称</label><input v-model="form.name"></div>'
new = '<div class="form-row"><label>设备名称</label><select v-model="form.name"><option value="">-- 请选择 --</option><option>打印机</option><option>服务器</option><option>路由器</option><option>主机</option><option>显示器</option><option>交换机</option></select></div>\n        <div class="form-row" v-if="form.name===\'打印机\'"><label>型号</label><input v-model="form.model"></div>'
c = c.replace(old, new)
open(f, 'w', encoding='utf-8').write(c)
print("done")
