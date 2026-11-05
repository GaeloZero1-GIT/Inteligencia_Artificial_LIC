import yaml
import re

def parse_atom(atom_str):
    match = re.match(r'([A-Za-z_]+)\((.+)\)', atom_str.strip())
    if match:
        pred = match.group(1)
        args = [arg.strip() for arg in match.group(2).split(',')]
        return pred, args
    return None, None

def format_atom(pred, args):
    return f"{pred}({','.join(args)})"

def is_variable(term):
    return term[0].islower()

def unify_args(args1, args2, theta):
    if len(args1) != len(args2): return None
    new_theta = theta.copy()
    for a1, a2 in zip(args1, args2):
        if is_variable(a1) and not is_variable(a2):
            if a1 in new_theta and new_theta[a1] != a2: return None
            new_theta[a1] = a2
        elif not is_variable(a1) and is_variable(a2):
            if a2 in new_theta and new_theta[a2] != a1: return None
            new_theta[a2] = a1
        elif is_variable(a1) and is_variable(a2):
            if a1 != a2: new_theta[a1] = a2
        else:
            if a1 != a2: return None
    return new_theta

def apply_theta(args, theta):
    return [theta.get(arg, arg) for arg in args]

def forward_chain(kb):
    facts = kb.get('facts', []).copy()
    rules = kb.get('rules', [])
    
    parsed_facts = [parse_atom(f) for f in facts]
    new_facts_this_round = True
    derived_atoms = []
    
    print("\n--- ENCADENAMIENTO HACIA ADELANTE ---")
    
    while new_facts_this_round:
        new_facts_this_round = False
        current_facts = list(parsed_facts)
        
        for rule in rules:
            head_pred, head_args = parse_atom(rule['head'])
            body = [parse_atom(b) for b in rule['body']]
            
            thetas = [{}]
            for b_pred, b_args in body:
                next_thetas = []
                for theta in thetas:
                    sub_b_args = apply_theta(b_args, theta)
                    for f_pred, f_args in current_facts:
                        if f_pred == b_pred:
                            new_theta = unify_args(sub_b_args, f_args, theta)
                            if new_theta is not None:
                                next_thetas.append(new_theta)
                thetas = next_thetas
                
            for theta in thetas:
                if theta:
                    new_head_args = apply_theta(head_args, theta)
                    if not any(is_variable(arg) for arg in new_head_args):
                        if (head_pred, new_head_args) not in parsed_facts:
                            parsed_facts.append((head_pred, new_head_args))
                            derived_atom = format_atom(head_pred, new_head_args)
                            derived_atoms.append(derived_atom)
                            new_facts_this_round = True
                            print(f"Derivado: {derived_atom} usando {rule['id']}")
    
    return derived_atoms, [format_atom(p, a) for p, a in parsed_facts]

def backward_chain(kb, query_str):
    facts = [parse_atom(f) for f in kb.get('facts', [])]
    rules = kb.get('rules', [])
    q_pred, q_args = parse_atom(query_str)
    
    print(f"\n--- ENCADENAMIENTO HACIA ATRÁS: {query_str} ---")
    
    def bc_or(goal_pred, goal_args, theta, visited_goals):
        goal_str = format_atom(goal_pred, apply_theta(goal_args, theta))
        if goal_str in visited_goals:
            return None
            
        new_visited = visited_goals | {goal_str}
        
        for f_pred, f_args in facts:
            if f_pred == goal_pred:
                new_theta = unify_args(apply_theta(goal_args, theta), f_args, theta)
                if new_theta is not None:
                    print(f"Probado con hecho: {format_atom(f_pred, f_args)}")
                    return new_theta
                    
        for rule in rules:
            head_pred, head_args = parse_atom(rule['head'])
            if head_pred == goal_pred:
                new_theta = unify_args(apply_theta(goal_args, theta), head_args, theta)
                if new_theta is not None:
                    print(f"Prueba {rule['id']} para {goal_str}...")
                    final_theta = bc_and(rule['body'], new_theta, new_visited)
                    if final_theta is not None:
                        print(f"Éxito con {rule['id']} para {goal_str}")
                        return final_theta
                    else:
                        print(f"Fallo con {rule['id']} para {goal_str}")
        return None

    def bc_and(body, theta, visited_goals):
        if not body: return theta
        first_pred, first_args = parse_atom(body[0])
        rest = body[1:]
        
        new_theta = bc_or(first_pred, first_args, theta, visited_goals)
        if new_theta is not None:
            return bc_and(rest, new_theta, visited_goals)
        return None

    result_theta = bc_or(q_pred, q_args, {}, set())
    if result_theta is not None:
        print(f"Resultado: PROBADA")
        return True
    else:
        print(f"Resultado: FALLÓ")
        return False

if __name__ == "__main__":
    with open("biblioteca.yaml", "r") as f:
        kb = yaml.safe_load(f)
        
    forward_chain(kb)
    
    queries = ["AccesoNoche(Ana)", "AccesoNoche(Luis)", "AccesoNoche(Marta)"]
    for q in queries:
        backward_chain(kb, q)