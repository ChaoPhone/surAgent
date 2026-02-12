import sys

from Core.engine import load_agents, run_main_loop

if __name__ == "__main__":
    print("🔄 初始化蜂群系统...")
    load_agents()
    print("✅ 系统就绪。")
    while True:
        try:
            user_input = input("\n🙋 召唤师指令: ").strip()
            if user_input.lower() in ['q', 'exit']:
                break
            if not user_input:
                continue
            run_main_loop(user_input)
        except KeyboardInterrupt:
            sys.exit(0)
        except Exception as e:
            print(f"Error: {e}")
