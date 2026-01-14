import json
import urllib.request

# 两个远程文件 URL
URLS = [
    "https://raw.githubusercontent.com/qichiyuhub/rule/refs/heads/main/config/singbox/1.12.x/sub-momofake.json",
    "https://raw.githubusercontent.com/manlongdan/rule_set/refs/heads/main/config/my_sub_momo.json"
]

def fetch_json(url):
    print(f"⬇️ 正在下载: {url} ...")
    try:
        # 还原为原版：不带 timeout，不忽略 SSL
        with urllib.request.urlopen(url) as response:
            return json.load(response)
    except Exception as e:
        print(f"❌ 下载或解析失败 [{url}]: {e}")
        exit(1)

# 1. 读取配置
base = fetch_json(URLS[0])
custom = fetch_json(URLS[1])

# =======================================================
# 2. 动态修改 "🧠 AI" 出站组 (保留原版 Append 逻辑)
# =======================================================
target_tag = "🧠 AI"
new_outbound = "🐸 手动选择"
modified = False

if "outbounds" in base:
    for outbound in base["outbounds"]:
        if outbound.get("tag") == target_tag:
            if "outbounds" not in outbound:
                outbound["outbounds"] = []
            
            if new_outbound not in outbound["outbounds"]:
                # 原版 PDF 使用的是 append (追加到末尾)
                outbound["outbounds"].append(new_outbound)
                modified = True
                print(f"✅ AI组: 已追加 '{new_outbound}'")
            else:
                print(f"ℹ️ 提示: '{target_tag}' 组中已包含 '{new_outbound}'，跳过添加")
            break

# =======================================================
# 3. 合并 rule_set (原版逻辑)
# =======================================================
base_route = base.setdefault("route", {})
custom_route = custom.get("route", {})

base_rule_sets = {r["tag"]: r for r in base_route.get("rule_set", [])}
custom_rule_sets = {r["tag"]: r for r in custom_route.get("rule_set", [])}

base_rule_sets.update(custom_rule_sets)
base_route["rule_set"] = list(base_rule_sets.values())

# =======================================================
# 4. 合并路由规则 (Rules)
# =======================================================
base_rules = base_route.get("rules", [])
custom_rules = custom_route.get("rules", [])

# 【必要修改】: 必须插到最前 (custom + base)，否则直连会被覆盖失效
final_rules = custom_rules + base_rules 
base_route["rules"] = final_rules
print(f"✅ 路由规则: 自定义规则已置顶")

# =======================================================
# 5. 【新增】合并 DNS 规则
# =======================================================
base_dns = base.setdefault("dns", {})
base_dns_rules = base_dns.get("rules", [])

if "dns" in custom and "rules" in custom["dns"]:
    custom_dns_rules = custom["dns"]["rules"]
    
    # 逻辑: 让自定义 DNS 规则优先匹配
    base_dns["rules"] = custom_dns_rules + base_dns_rules
    print(f"✅ DNS规则: 已合并 {len(custom_dns_rules)} 条自定义 DNS 规则")
else:
    print(f"ℹ️ 提示: my_sub_momo.json 未发现 DNS 规则")

# =======================================================
# 6. 输出
# =======================================================
output_filename = "merged_momo.json"
with open(output_filename, "w", encoding="utf-8") as f:
    json.dump(base, f, ensure_ascii=False, indent=2)

print(f"🎉 生成成功 -> {output_filename}")
