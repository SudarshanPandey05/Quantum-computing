import random
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from qiskit.quantum_info import Statevector

# function for getting user bits for multiple qubits
def get_user_bits_multi(num_bits, entity_name):
    while True:
        bits_str = input(f"Enter {num_bits} binary bits for {entity_name} (e.g., 01010101): ")
        if len(bits_str) == num_bits and all(bit in '01' for bit in bits_str):
            return [int(bit) for bit in bits_str]
        else:
            print(f"Invalid input. Please enter exactly {num_bits} binary bits.")

def get_user_bases_multi(num_bits, entity_name):
    while True:
        bases_str = input(f"Enter {num_bits} bases for {entity_name} (0 for +, 1 for x, e.g., 01100110): ")
        if len(bases_str) == num_bits and all(base in '01' for base in bases_str):
            return [int(base) for base in bases_str]
        else:
            print(f"Invalid input. Please enter exactly {num_bits} bases (0 or 1).")

# 1. Sam's Transmission (using multiple qubits)
def Sam_transmission_multi_qubit(Sam_bits, Sam_bases):
    num_bits = len(Sam_bits)
    num_qubits = num_bits  # Each bit will be on a separate qubit
    qc = QuantumCircuit(num_qubits, num_qubits)
    ''' '''
    Sam_transmitted_circuits = []

    for i in range(num_qubits):
        bit = Sam_bits[i]
        basis = Sam_bases[i]

        if basis == 0:  # Rectilinear basis (+)
            if bit == 1:
                qc.x(i)
        else:  # Diagonal basis (x)
            if bit == 0:
                qc.h(i)
            else:
                qc.h(i)
                qc.z(i)
    Sam_transmitted_circuits.append(qc) # Only one circuit for all transmitted qubits
    return Sam_transmitted_circuits

# 2. Ron's Measurement (using multiple qubits and simulated noise)
def Ron_measurement_multi_qubit_with_noise(transmitted_circuits, Ron_bases, noise_probability=0.1):
    Ron_results = []
    simulator = AerSimulator()
    qc = transmitted_circuits[0].copy() # Get the single multi-qubit circuit
    num_qubits = qc.num_qubits

    for i in range(num_qubits):
        basis = Ron_bases[i]
        if basis == 1:  # Diagonal basis (x) measurement
            qc.h(i)
        qc.measure(i, i)

    compiled_circuit = transpile(qc, simulator)
    job = simulator.run(compiled_circuit, shots=1)
    result = job.result()
    counts = result.get_counts(qc)
    measured_str = list(counts.keys())[0] # Get the measured bit string
    measured_bits = [int(bit) for bit in reversed(measured_str)] # Reverse to match qubit order

    noisy_results = []
    for bit in measured_bits:
        if random.random() < noise_probability:
            noisy_results.append(1 - bit)
        else:
            noisy_results.append(bit)

    return noisy_results

# 3. Basis Reconciliation (remains the same logic)
def basis_reconciliation(Sam_bases, Ron_bases, Sam_bits, Ron_results):
    shared_key_Sam = []
    shared_key_Ron = []
    for i in range(len(Sam_bases)):
        if Sam_bases[i] == Ron_bases[i]:
            shared_key_Sam.append(Sam_bits[i])
            shared_key_Ron.append(Ron_results[i])
    return shared_key_Sam, shared_key_Ron

# --- Main Execution with User Input and Noise (Multiple Qubits) ---
num_bits = 29  # Example with 8 bits (and thus 8 qubits)
noise_level = 0

# Sam's step
print("--- Sam's Input ---")
Sam_bits = get_user_bits_multi(num_bits, "Sam")
Sam_bases = get_user_bases_multi(num_bits, "Sam")
Sam_transmitted_circuits = Sam_transmission_multi_qubit(Sam_bits, Sam_bases)
print("\nSam's generated bits:", Sam_bits)
print("\nSam's chosen bases:", Sam_bases)

# Ron's step
print("\n--- Ron's Input ---")
Ron_bases = get_user_bases_multi(num_bits, "Ron")
Ron_measured_results = Ron_measurement_multi_qubit_with_noise(Sam_transmitted_circuits, Ron_bases, noise_level)
print("\nRon's chosen bases:", Ron_bases)
print("\nRon's measurement results:", Ron_measured_results)

# Basis reconciliation
shared_key_Sam, shared_key_Ron = basis_reconciliation(Sam_bases, Ron_bases, Sam_bits, Ron_measured_results)

print("\nShared key (Sam):", shared_key_Sam)
print("\nShared key (Ron):", shared_key_Ron)

print("\nLength of Sam's raw key:", len(Sam_bits))
print("\nLength of Ron's raw measurements:", len(Ron_measured_results))
print("\nLength of shared raw key:", len(shared_key_Sam))

# Verify if the shared keys match (now accounting for noise)
if shared_key_Sam == shared_key_Ron:
    print("\nShared keys match!")
else:
    print("\nShared keys do NOT match (due to simulated noise or different user inputs).")