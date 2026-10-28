import sys

sys.path.insert(0, "D:/EAG-GUARD/src")
from agentdojo.functions_runtime import FunctionsRuntime
from agentdojo.task_suite.load_suites import get_suite

samples = {
    "slack": [
        ("read_channel_messages", {"channel": "general"}),
        ("read_inbox", {"user": "Bob"}),
        ("get_channels", {}),
    ],
    "workspace": [
        ("search_emails", {"query": "report"}),
        ("list_files", {}),
        ("get_received_emails", {}),
    ],
    "travel": [
        ("get_all_hotels_in_city", {"city": "Paris"}),
        ("get_rating_reviews_for_hotels", {"hotel_names": ["Le Marais Boutique"]}),
    ],
}

for domain, calls in samples.items():
    suite = get_suite("v1", domain)
    env = suite.load_and_inject_default_environment({})
    runtime = FunctionsRuntime(suite.tools)
    print(f"########## {domain}")
    for name, args in calls:
        try:
            result, error = runtime.run_function(env, name, args)
        except Exception as exc:  # noqa: BLE001
            print(f"-- {name}: 异常 {exc}")
            continue
        text = str(result)
        print(f"-- {name}({args}) error={error}")
        print("   ", text[:420].replace("\n", "\\n"))
    print()
