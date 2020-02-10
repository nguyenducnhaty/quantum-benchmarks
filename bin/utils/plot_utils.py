import pandas as pd
import os
import json

ROOT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
IMAGE_PATH = os.path.join(ROOT_PATH, 'images')

COLOR = {
    'yao': 'tab:red',
    'yao (cuda)': 'tab:orange',
    'yao x 1000': 'tab:blue',
    'yao x 64': 'tab:blue',
    'qiskit': 'tab:green',
    'qiskit (cuda)': 'tab:gray',
    'projectq': 'tab:blue',
    'cirq': 'tab:cyan',
    'quest': 'tab:olive',
    'qulacs': 'tab:brown',
    'qulacs (cuda)': 'tab:pink',
    'pennylane': 'tab:purple',
}

def image_path(name):
    if not os.path.isdir(IMAGE_PATH):
        os.makedirs(IMAGE_PATH, exist_ok=True)
    return os.path.join(IMAGE_PATH, name)

def find_json(name):
    """find the first matchable json benchmark file.
    """
    benchmark_dir = os.path.join(ROOT_PATH, '.benchmarks')
    benchmark_path = os.path.join(benchmark_dir, os.listdir(benchmark_dir)[0])
    file_stack = []
    for each in os.listdir(benchmark_path):
        if name in each:
            file_stack.append(each)
    return os.path.join(benchmark_path, file_stack[-1])


def wash_benchmark_data(name, labels):
    """process benchmark data, append `inf` to the data if there is no such data (it means
    timeout during benchmarking usually). Then return a Pandas.DataFrame object.
    """
    with open(find_json(name)) as f:
        data = json.load(f)

    cols = [each['params']['nqubits'] for each in data['benchmarks'] if each['group'] == labels[0]]
    dd = {}
    dd['nqubits'] = cols
    for lb in labels:
        time_data = [each['stats']['min']*1e9
            for each in data['benchmarks'] if each['group'] == lb]
        if len(time_data) is not len(cols):
            time_data.append([float('inf') for _ in range(len(cols) - len(time_data) + 1)])

        dd[lb] = time_data
    return pd.DataFrame(data=dd)


def parse_data(packages, labels=['X', 'H', 'T', 'CNOT', 'Toffoli']):
    """parse benchmark data of `packages` of `labels`.
    """
    gate_data = {}
    for each_package in packages:
        if each_package == 'yao':
            if len(labels) == 1 and 'QCBM' in labels:
                pd_data = pd.read_csv(os.path.join(ROOT_PATH, 'yao_qcbm.csv'))
                gate_data[each_package] = pd_data[['nqubits', 'QCBM']]
                gate_data['yao (cuda)'] = pd_data[['nqubits', 'QCBM_cuda']].rename(columns={'QCBM_cuda' : 'QCBM'})
            elif len(labels) == 1 and 'QCBM (batch)' in labels:
                pd_data = pd.read_csv(os.path.join(ROOT_PATH, 'yao_qcbm_batch.csv'))
                gate_data['yao'] = pd_data[['nqubits', 'QCBM_batch']].rename(columns={'QCBM_batch' : 'QCBM (batch)'})
                gate_data['yao (cuda)'] = pd_data[['nqubits', 'QCBM_cuda_batch']].rename(columns={'QCBM_cuda_batch' : 'QCBM (batch)'})
            else:
                gate_data[each_package] = pd.read_csv(os.path.join(ROOT_PATH, 'yao.csv'))
        elif each_package == 'qulacs':
            if len(labels) == 1 and 'QCBM' in labels:
                gate_data['qulacs'] = wash_benchmark_data(each_package, ['QCBM'])
                gate_data['qulacs (cuda)'] = wash_benchmark_data(each_package, ['QCBM (cuda)']).rename(columns={'QCBM (cuda)': 'QCBM'})
            else:
                gate_data[each_package] = wash_benchmark_data(each_package, labels)
        elif each_package == 'qiskit':
            if len(labels) == 1 and 'QCBM' in labels:
                gate_data['qiskit'] = wash_benchmark_data(each_package, ['QCBM'])
                gate_data['qiskit (cuda)'] = wash_benchmark_data(each_package, ['QCBM (cuda)']).rename(columns={'QCBM (cuda)': 'QCBM'})
            else:
                gate_data[each_package] = wash_benchmark_data(each_package, labels)
        else:
            gate_data[each_package] = wash_benchmark_data(each_package, labels)

    return gate_data


def plot_absolute(ax, data : dict, gate):
    ls, labels = [], []
    for k in data:
        d = data[k]
        
        if k == 'yao':
            ls.append(ax.semilogy(d["nqubits"], d[gate], '-o', markersize=4, color=COLOR[k]))
        elif k == 'yao (cuda)':
            ls.append(ax.semilogy(d["nqubits"], d[gate], '-o', markersize=4, color=COLOR[k]))
        else:
            ls.append(ax.semilogy(d["nqubits"], d[gate], '-o', markersize=4, color=COLOR[k]))
        
        if k == 'quest':
            labels.append('pyquest-cffi')
        else:
            labels.append(k)

    ax.set_xlabel("nqubits", size=16)
    ax.set_ylabel("ns", size=16)
    return ls, labels


def plot_relative(ax, data: dict, gate, to='yao', log=True):
    ls, labels = [], []
    d_yao = data[to]
    for k in data:
        if k == to:
            continue
        else:
            d = data[k]
            if log:
                ls.append(ax.semilogy(d["nqubits"], d[gate]/d_yao[gate], '-o', markersize=4, color=COLOR[k]))
            else:
                ls.append(ax.plot(d["nqubits"], d[gate]/d_yao[gate], '-o', markersize=4, color=COLOR[k]))
            
            if k == 'quest':
                labels.append('pyquest-cffi')
            else:
                labels.append(k)

    ax.axhline(y=1, linestyle='--')
    labels.append(to)
    ax.set_xlabel("nqubits", size=16)
    ax.set_ylabel("relative time ({} = 1)".format(to), size=16)
    return ls, labels
