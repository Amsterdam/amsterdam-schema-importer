import graph
from datasets.service import DatasetService
service = DatasetService()

def n(o):
    return o.__name__

def c(f):
    annos = f.__annotations__
    event_in = annos['event']
    event_out = annos.get('return')

    result = f"""
    {n(f)}[shape=record;label=<<font point-size="25">{n(f)}</font><br/>{f.__doc__ or ""}>]
    {n(event_in)} -> {n(f)};
    """
    if event_out:
        result += f"""
    {n(f)} -> {n(event_out)};
        """
    return result

dot = [
    c(f) for f in service.registry.values()
]

print("""
digraph D {
""")
print("\n".join(dot))
print("""
}
""")
