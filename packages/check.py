import pkgutil, importlib
failures = []
for finder, name, ispkg in pkgutil.walk_packages(['packages/modules'], prefix='modules.'):
    try:
        importlib.import_module(name)
    except Exception as e:
        failures.append((name, repr(e)))
if failures:
    for n, err in failures:
        print(n, err)
else:
    print("No import-time errors found.")