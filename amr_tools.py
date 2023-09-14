from nltk import ngrams
import re 
import penman

def flatten_amr(graph):
    # Turns the AMR graph to lAMR, i.e. condences the graph to one line
    graph = re.sub(r'\s+', ' ', graph) # Remove change of lines
    graph = re.sub('(# ::snt .*?) (\([\w\n]+ /)', '' + r"\2", graph) # Remove sentence
    graph = re.sub('(\"[\w\d-]*)[\(|\)]+([\w\d-]*")', r'\1' + r'\2', graph) # Remove wild parentheses
    graph = re.sub('(\"[\w\d\s]*)\(([\w\d\s]*)\)([\w\d\s]*")', r'\1\2\3', graph) # Remove wild parentheses
    
    return graph

def find_arg(graph, node):
    # Returns am argument of a graph that comes after a specific node (e.g. 'ARG0', 'time', etc.)
    substring = graph.partition(':' + node + ' ')[2]
    parenth = 0
    arg = ''
    for s in substring:
        if s == '(':
            parenth +=1
        elif s ==')':
            parenth -=1
        arg += s
        if parenth == 0:
            break
    return arg

def extract_arguments(graph):
    # Splits the AMR graph into all possible arguments and returns a list of lists, each containing:
    # 0) the argument's variable,
    # 1) the argument's root, 
    # 2) the argument, and
    # 3) the level of the argument's depth, e.g. the whole graph has depth 0, its immediate arguments have level 1, etc.
    graph = flatten_amr(graph)
    # graph = re.sub('"(.*?)"', '\" \"', graph)
    finished = list()
    stack = list()
    top_idx = 0
    for c in graph:
        for i in range(top_idx):
            stack[i] = stack[i] + c
        if c == '(':
            stack.append('(')
            top_idx += 1
        elif c == ')':
            argument = stack[top_idx-1]
            argument = re.sub(r'\s+', ' ', argument)
            signature = re.findall(r'\(([\w\d]+) / ', argument)[0]
            main_pred = re.findall(r'\([\w\d]+ / ([\w\d-]+)', argument)[0]
            finished.append([signature, main_pred, argument, top_idx-1])
            del stack[top_idx-1]
            top_idx -= 1
    return finished

def find_argument_after(graph, arg):
    arg_pos = graph.find(':' + arg)
    
    new_graph = ''
    top_idx = int()
    for c in graph[arg_pos + len(arg) +2 :]:
        new_graph += c
        if c == '(':
            top_idx +=1
        if c == ')':
            top_idx -=1
        if top_idx == 0:
            break
    return new_graph

def remove_arg(graph, node):
    if node in graph:
        arg = find_arg(graph, node + ' ')
        graph = graph.replace(' :' + node + ' ' + arg, '')
    
    return graph

def develop_subgraph(graph, subgraph):
    # Replaces variables in a subgraph into their corresponding subgraphs
    args = extract_arguments(graph)
    loose_var = re.findall(':[\w\d]+ (\w\d?)', subgraph) # locatte variables to be developed
   
    for a in args:
        subgraph = re.sub("(:[\w\d]+)" + " " + a[0] , r"\1 " + a[2] , subgraph, 1)

    return subgraph

def extract_developed_arguments(graph): 
    # Returns a list of argument graphs, with variables developed to their subgraphs    
    args = extract_arguments(graph)
    for a in args:
        a[2] = develop_subgraph(graph, a[2])
    return args

def create_argdict(graphs):
    # Creates a dictionary with numbered sents for keys and a list of their arguments for values
    argdict = dict()
    sen_counter = 0
    for a in graphs:
        x = extract_developed_arguments(a)
        argdict[f'sen_{sen_counter}'] = x
        sen_counter +=1
    return argdict

def preds_args_list(graph):
    # Returns two lists, one with all the predicates of the graph, and one with the rest of the arguments
    content = extract_arguments(graph)
    preds = []
    args = []
    for c in content:
        x = re.findall('\w+-\d+', c[1])
        if len(x) > 0:
            preds.append(c[1])
        else:
            args.append(c[1])
        # print(c[1])
    return preds, args

def sentence_as_preds(graph):
    # Returns a string containing all predicates of the graph, e.g.:
    # 'I have a cat" --> "have-03"
    preds = re.findall('[a-z]*-*[a-z]+-\d+', graph)
    sent_as_preds = ''
    for p in preds:
        sent_as_preds = sent_as_preds + p + ' '
    return sent_as_preds

def sentence_as_args(graph):
    # Returns a string containing all arguments of the graph, e.g.:
    # 'I have a cat" --> "have-03 I cat"
    args = extract_arguments(graph)
    args_list = [a[1] for a in args]
        
    graph = flatten_amr(graph)
    graphl = graph.split()
    new_args = []
    
    for l in graphl:
        for a in args_list:
            if a in l:
                new_args.append(a)
    
    Xnew_args = ['X'] + new_args
    # new_new_args = []
    sent_as_args = ''
    for a,b in zip(new_args, Xnew_args):
        if not a == b:
            # new_new_args.append(a)
            sent_as_args = sent_as_args + a + ' '

    return sent_as_args

def get_npreds(graph, int):
    # Returns a list of tuples containing n number of approximate predicates, similar to ngrams
    preds = sentence_as_preds(graph)
    npreds = list(ngrams(preds.split(), int))
    return npreds

def envelop_arguments(graph):
    # replaces arguments with their signatures (e.g. (u / use-01 :ARG1 c :purpose d) )
    graph = flatten_amr(graph)
    args = extract_arguments(graph)

    for a in args:
        if a[3] == 1:
            graph = graph.replace(' ' + a[2], ' ' + a[0])

    return graph

def graph_to_dict(graph):
    # Turns the graph into dictionary form, with the argument as key and its constituents as values
    argdict = {}
    final_dict = {}
    graph = flatten_amr(graph)
    args = extract_developed_arguments(graph)
    main_pred = args[-1][1]
    env_graph = envelop_arguments(graph)
    nodes = re.findall(':(.+?) ', env_graph)
    for n in nodes:
        if main_pred == 'name':
            arg_sig = re.findall(n + ' \"(.*?)\"', env_graph)
        else:
            arg_sig = re.findall(n + ' ([\w\d-]+)', env_graph)[0]
            for a in args:
                if arg_sig == a[0]:
                    arg_sig = a[2]
        argdict[n] = arg_sig
        final_dict[main_pred] = argdict
    return final_dict

def change_root(graph):
    args = extract_arguments(graph)
    
    preds = []
    for a in args:
        if '-' in a[1]:
            preds.append(a[0])
            
    pgraph = penman.decode(graph)
    new_graph = penman.encode(pgraph, top=preds[0])
    
    return new_graph

def mask_variables(graph):
    # Replaces all variables with X
    graphx = re.sub('\([\w\d]+', '(X', graph)
    graphx = re.sub('(:[\w\d-]+ )[\w\d]+', r'\1X', graphx)
    return graphx 

def lamr_to_amr(graph):
    # Turns a line-AMR format to penman AMR
    root_var = re.findall("\(([\w\d]+)", graph)[0]
    
    pgraph = penman.decode(graph)
    new_graph = penman.encode(pgraph, top=root_var)

    return new_graph

def break_multisentences(graph):
    # Breaks graphs marked as multisentence to it's sentences
    new_graphs = []
    
    parag = re.findall(':snt (.*)', graph)[0]
    args = graph_to_dict(graph)
  
    graphs = [args['multi-sentence'][a] for a in args['multi-sentence']]
    sents = parag.split('.')[:-1]
    
    for s, g in zip(sents, graphs):    
        new_g = "# ::snt " + s + '.\n' + lamr_to_amr(g)
        new_graphs.append(new_g)
    
    return new_graphs
