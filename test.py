import amr_tools

graph = open('sample_graph.txt', 'r', encoding='utf8').read()
print('GRAPH')
print(graph)
print()

# Return the 'time' argument of 'contrast-01':
argument = amr_tools.find_arg(graph, 'time')
print('RETURN SPECIFIC ARGUMENT:')
print(argument)
print()

# AMR to line-AMR:
lgraph = amr_tools.flatten_amr(graph)
print('LINE AMR:')
print(lgraph)
print()

# Represent graph as dictionary:
dict_graph = amr_tools.graph_to_dict(graph)
print('GRAPH TO DICTIONARY:')
print(dict_graph)
print()

# Graph with masked variables
mask_graph = amr_tools.mask_variables(graph)
print('MASKED VARIABLES:')
print(mask_graph)
print()

