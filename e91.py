import random
import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from qiskit.quantum_info import Statevector
from scipy.stats import chisquare

# --- Define Measurement Bases in Qiskit ---
basis_hv = [[("rz", 0, 0)], [("rx", np.pi, 0)]]  # Z and X basis
basis_pm = [[("rz", np.pi/4, 0)], [("rz", -np.pi/4, 0)]] # +/- 45 degree basis
basis_circular = [[("ry", np.pi/4, 0), ("sx", 0, 0)], [("ry", -np.pi/4, 0), ("sx", 0, 0)]] # Approximate circular

all_bases = [basis_hv, basis_pm, basis_circular]
base_names = ["HV", "+/-", "Circular"]

# Measurement operators for Bell test (simplified to Pauli operators)
bell_ops = [("Z", "Z"), ("Z", "X"), ("X", "Z"), ("X", "X")]

def create_bell_pair(state="psi_minus"):
    """Creates Bell pairs with classical bits for measurement."""
    qc = QuantumCircuit(2, 2)  # Create a circuit with 2 qubits and 2 classical bits
    if state == "phi_plus":
        qc.h(0)
        qc.cx(0, 1)
    elif state == "phi_minus":
        qc.h(0)
        qc.cx(0, 1)
        qc.z(1)
    elif state == "psi_plus":
        qc.h(0)
        qc.cx(0, 1)
        qc.x(1)
    elif state == "psi_minus":
        qc.h(0)
        qc.cx(0, 1)
        qc.z(0)
        qc.x(1)
    return qc

def measure_qubit(circuit, qubit, basis, cbit):
    """Adds measurement gates based on the basis, measuring to a specific classical bit."""
    if basis == basis_hv:
        circuit.measure(qubit, cbit)
    elif basis == basis_pm:
        meas = QuantumCircuit(1, 1)
        meas.ry(-np.pi/4, 0)
        meas.measure(0, 0)
        circuit.compose(meas, qubits=[qubit], clbits=[cbit], inplace=True)
    elif basis == basis_circular:
        meas = QuantumCircuit(1, 1)
        meas.sdg(0)
        meas.h(0)
        meas.measure(0, 0)
        circuit.compose(meas, qubits=[qubit], clbits=[cbit], inplace=True)
    return circuit

def simulate_measurement(circuit, backend, shots=1):
    """Simulates measurement."""
    compiled_circuit = transpile(circuit, backend)
    job = backend.run(compiled_circuit, shots=shots, memory=True)
    result = job.result()
    measurements = result.get_memory(circuit)
    return measurements[0]

def evaluate_bell_statistic(bell_data):
    """A simplified way to estimate a Bell-like statistic."""
    correlations = []
    for (alice_basis_idx, alice_result), (bob_basis_idx, bob_result) in bell_data:
        a_val = 1 if alice_result == '0' else -1
        b_val = 1 if bob_result == '0' else -1

        # Consider specific basis combinations for a CHSH-like parameter
        if (alice_basis_idx == 0 and bob_basis_idx == 1) or \
           (alice_basis_idx == 0 and bob_basis_idx == 2) or \
           (alice_basis_idx == 1 and bob_basis_idx == 2) or \
           (alice_basis_idx == 1 and bob_basis_idx == 0) or \
           (alice_basis_idx == 2 and bob_basis_idx == 0) or \
           (alice_basis_idx == 2 and bob_basis_idx == 1):
            correlations.append(a_val * b_val)

    if correlations:
        return np.mean(correlations) * np.sqrt(2) # Rough estimate related to S in CHSH
    return 0

def get_bell_test_input_from_user(num_pairs):
    """Gets bell test data input from the user for a specified number of pairs."""
    bell_data = []
    print(f"Please enter the measurement results for {num_pairs} Bell pairs.")
    for i in range(num_pairs):
        print(f"\n--- Pair {i+1} ---")
        while True:
            try:
                alice_basis_idx = int(input("Enter Alice's basis index (0 for HV, 1 for +/- 45, 2 for Circular): "))
                if alice_basis_idx not in [0, 1, 2]:
                    print("Invalid basis index for Alice. Please enter 0, 1, or 2.")
                    continue

                alice_result = input("Enter Alice's measurement result ('0' or '1'): ")
                if alice_result not in ['0', '1']:
                    print("Invalid measurement result for Alice. Please enter '0' or '1'.")
                    continue

                bob_basis_idx = int(input("Enter Bob's basis index (0 for HV, 1 for +/- 45, 2 for Circular): "))
                if bob_basis_idx not in [0, 1, 2]:
                    print("Invalid basis index for Bob. Please enter 0, 1, or 2.")
                    continue

                bob_result = input("Enter Bob's measurement result ('0' or '1'): ")
                if bob_result not in ['0', '1']:
                    print("Invalid measurement result for Bob. Please enter '0' or '1'.")
                    continue

                bell_data.append(((alice_basis_idx, alice_result), (bob_basis_idx, bob_result)))
                break  # Move to the next pair
            except ValueError:
                print("Invalid input. Please enter an integer for the basis index.")
    return bell_data

def e91_protocol_qiskit_user_input():
    """Runs the E91 protocol using Bell test data input from the user."""
    while True:
        try:
            num_pairs = int(input("Enter the number of Bell pairs for the test: "))
            if num_pairs <= 0:
                print("Please enter a positive number of pairs.")
            else:
                break
        except ValueError:
            print("Invalid input. Please enter an integer for the number of pairs.")

    bell_test_data = get_bell_test_input_from_user(num_pairs)

    if not bell_test_data:
        print("No Bell test data provided.")
        return [], []

    # 3. Bell Inequality Test (Simplified CHSH-like)
    bell_statistic = evaluate_bell_statistic(bell_test_data)
    print(f"\nEstimated Bell-like statistic (S) from user input: {abs(bell_statistic):.2f}")

    bell_violation_threshold = 2.0  # Theoretical limit for classical correlations

    if abs(bell_statistic) > bell_violation_threshold:
        print("Bell inequality violated based on user input. Proceeding with (hypothetical) key generation.")
        # Since we don't have actual key generation with user input, we'll return a placeholder
        hypothetical_key = [random.randint(0, 1) for _ in range(len(bell_test_data) // 2)]
        return hypothetical_key, hypothetical_key
    else:
        print("Bell inequality not significantly violated based on user input. Possible eavesdropping or noise. Discarding (hypothetical) key.")
        return [], []

if __name__ == "__main__":
    alice_key, bob_key = e91_protocol_qiskit_user_input()

    if alice_key and bob_key and len(alice_key) == len(bob_key):
        print("\nSecure key exchange simulation (E91) with user input (hypothetical) successful.")
        print(f"Length of hypothetical final key: {len(alice_key)} bits")
        print(f"Alice's hypothetical key: {alice_key}")
        print(f"Bob's hypothetical key: {bob_key}")
    else:
        print("\nKey exchange simulation (E91) with user input failed or resulted in an empty key.")