import json
import re
import subprocess
import requests

OLLAMA_URL = "http://localhost:11434/api/generate"

print("==================================================")
print(" Windows AI Agent")
print("==================================================")

MODEL_NAME = input(" 請輸入你想使用的模型名稱: ").strip()


def get_ai_commands(user_prompt):
    system_prompt = (
        "你是一個 Windows 系統自動化 Agent。\n"
        "請根據使用者的需求，規劃出正確的 PowerShell 指令。\n"
        "你只能輸出一個標準的 JSON 格式（可以是物件 {} 或陣列 []），內部必須包含 type 和 command 欄位。\n"
        "不要包含任何 Markdown 語法（不要 ```json），不要有任何前後解釋。\n\n"
        "格式範例：\n"
        '{"type": "powershell", "command": "Start-Process notepad"}'
    )

    payload = {
        "model": MODEL_NAME,
        "prompt": f"{system_prompt}\n\n使用者需求：{user_prompt}",
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0.1,  
            "top_p": 0.1
        }
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload)
        raw_response = response.json().get("response", "").strip()

        # 尋找最外層的 JSON 結構，不管是 [ ] 還是 { } 
        match = re.search(r'([\[{].*[\]}])', raw_response, re.DOTALL)
        if not match:
            return []

        clean_json = match.group(1)
        data = json.loads(clean_json)

        # 如果 AI 吐的是單一物件 {}，手動把它包成清單 []，方便後面統一處理
        if isinstance(data, dict):
            return [data]
        return data
            
    except Exception as e:
        print(f" JSON 解析失敗: {e}")
        return []


def execute_system_commands(commands):
    print("\n [Agent] 開始執行指令...")
    for idx, cmd in enumerate(commands, 1):
        if not isinstance(cmd, dict):
            continue
        cmd_type = cmd.get("type")
        command = cmd.get("command", "")

        if cmd_type == "powershell" and command:
            print(f" 執行指令: {command}")
            try:
                # 判斷是否為需要看結果的指令
                if any(x in command for x in ["Get-ChildItem", "ping", "dir", "ipconfig"]):
                    result = subprocess.run(["powershell", "-Command", command], capture_output=True, text=True)
                    if result.returncode == 0:
                        print(f"\n [執行結果]:\n{result.stdout}")
                    else:
                        print(f"  執行回傳錯誤: {result.stderr}")
                else:
                    subprocess.Popen(["powershell", "-Command", command], 
                                     stdout=subprocess.DEVNULL, 
                                     stderr=subprocess.DEVNULL)
                    print("  指令已成功下達！")
            except Exception as e:
                print(f" 執行失敗: {e}")
    print("任務交辦完成！")


if __name__ == "__main__":
    while True:
        try:
            print("\n" + "="*50)
            user_input = input(" 請輸入指令: ").strip()
            if not user_input:
                continue

            print(f" 正在讓 {MODEL_NAME} 生成指令...")
            action_steps = get_ai_commands(user_input)

            if action_steps:
                execute_system_commands(action_steps)
            else:
                print(" 無法從 AI 取得有效指令。")
                
        except KeyboardInterrupt:
            print("\n 系統關閉。")
            break
