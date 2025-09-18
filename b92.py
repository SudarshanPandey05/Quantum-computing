import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from qiskit.quantum_info import Statevector

def encode_b92_with_alice_basis(alice_bits, alice_bases):
    """Encodes a bit string into B92 quantum states based on Alice's bases."""
    qc = QuantumCircuit(len(alice_bits), len(alice_bits))
    for i, (bit, basis) in enumerate(zip(alice_bits, alice_bases)):
        if basis == 0:  # Alice chooses '0' basis (implicitly |H>)
            if bit == '1':
                raise ValueError("Inconsistent input: bit '1' with basis '0' in B92")
            # Encode '0' as |H> (no operation needed)
        elif basis == 1:  # Alice chooses '1' basis (implicitly |+>)
            if bit == '0':
                raise ValueError("Inconsistent input: bit '0' with basis '1' in B92")
            # Encode '1' as |+>
            qc.h(i)
        else:
            raise ValueError("Invalid Alice's basis. Must be 0 or 1 for B92.")
    return qc


def measure_b92(circuit, num_qubits, measurement_bases):
    """Measures B92 encoded qubits in given bases."""
    meas = QuantumCircuit(num_qubits, num_qubits)
    bob_results = []
    for i, basis in enumerate(measurement_bases):
        if basis == 0:  # Measure in {|V>, |H>} basis (Z basis)
            meas.measure(i, i)
        elif basis == 1:  # Measure in {|->, |+>} basis (X basis after Hadamard)
            meas.h(i)
            meas.measure(i, i)
        else:
            raise ValueError("Invalid measurement basis. Must be 0 or 1.")

    combined_circuit = circuit.compose(meas)
    simulator = AerSimulator()
    compiled_circuit = transpile(combined_circuit, simulator)
    job = simulator.run(compiled_circuit, shots=1, memory=True)
    result = job.result()
    measurement = result.get_memory(combined_circuit)[0]
    return measurement

def get_user_alice_bases(num_bits):
    """Gets Alice's bases from the user."""
    while True:
        bases_str = input(f"Enter Alice's bases for {num_bits} bits (0 or 1, e.g., 0110): ").strip()
        if len(bases_str) == num_bits and all(base in ['0', '1'] for base in bases_str):
            return [int(base) for base in list(bases_str)]
        else:
            print(f"Invalid input. Please enter a string of {num_bits} '0's and '1's.")

def get_user_alice_bits(num_bits):
    """Gets Alice's bits from the user."""
    while True:
        bits_str = input(f"Enter Alice's secret bits for {num_bits} transmissions (0 or 1, e.g., 0110): ").strip()
        if len(bits_str) == num_bits and all(bit in ['0', '1'] for bit in bits_str):
            return list(bits_str)
        else:
            print(f"Invalid input. Please enter a string of {num_bits} '0's and '1's.")

def get_user_bob_bases(num_bits):
    """Gets Bob's measurement bases from the user."""
    while True:
        bases_str = input(f"Enter Bob's measurement bases for {num_bits} bits (0 for Z, 1 for X, e.g., 0110): ").strip()
        if len(bases_str) == num_bits and all(base in ['0', '1'] for base in bases_str):
            return [int(base) for base in list(bases_str)]
        else:
            print(f"Invalid input. Please enter a string of {num_bits} '0's and '1's.")

def b92_protocol_user_input_bases_bits_bob():
    """Simulates the B92 QKD protocol with separate user input for Alice's bases, bits, and Bob's bases."""
    while True:
        try:
            num_bits = int(input("Enter the number of transmissions: "))
            if num_bits > 0:
                break
            else:
                print("Please enter a positive number of transmissions.")
        except ValueError:
            print("Invalid input. Please enter an integer.")

    alice_bases = get_user_alice_bases(num_bits)
    alice_bits = get_user_alice_bits(num_bits)
    bob_measurement_bases = get_user_bob_bases(num_bits)

    alice_sent_states = []
    for basis in alice_bases:
        if basis == 0:
            alice_sent_states.append('H')
        elif basis == 1:
            alice_sent_states.append('+')
        else:
            raise ValueError("Invalid Alice's basis.")

    try:
        quantum_channel = encode_b92_with_alice_basis(alice_bits, alice_bases)
    except ValueError as e:
        print(f"Error during encoding: {e}")
        return "", ""

    bob_measurements = measure_b92(quantum_channel, num_bits, bob_measurement_bases)

    bob_received_bits = []
    bob_conclusive_indices = []

    print("\n--- Transmission and Measurement ---")
    print(f"Number of transmissions: {num_bits}")
    print(f"Alice's bases:          {alice_bases}")
    print(f"Alice's bits:           {''.join(alice_bits)}")
    print(f"Alice's sent states:    {''.join(alice_sent_states)}")
    print(f"Bob's measurement bases: {bob_measurement_bases}")
    print(f"Bob's raw measurements:  {bob_measurements}")

    # Bob keeps only conclusive measurements
    for i in range(num_bits):
        alice_state = alice_sent_states[i]
        bob_basis = bob_measurement_bases[i]
        bob_result = bob_measurements[i]

        if alice_state == 'H' and bob_basis == 1 and bob_result == '1':
            bob_received_bits.append('0')
            bob_conclusive_indices.append(i)
        elif alice_state == '+' and bob_basis == 0 and bob_result == '1':
            bob_received_bits.append('1')
            bob_conclusive_indices.append(i)
        else:
            pass # Inconclusive result

    print("\n--- Key Generation ---")
    print(f"Bob's conclusive measurement indices: {bob_conclusive_indices}")
    print(f"Bob's received bits (raw key):     {''.join(bob_received_bits)}")

    agreed_alice_key = [alice_bits[i] for i in bob_conclusive_indices]
    print(f"Alice's corresponding bits (raw key): {''.join(agreed_alice_key)}")

    final_key_alice = "".join(agreed_alice_key)
    final_key_bob = "".join(bob_received_bits)

    return final_key_alice, final_key_bob

if __name__ == "__main__":
    alice_final_key, bob_final_key = b92_protocol_user_input_bases_bits_bob()

    print("\n--- Final Key ---")
    print(f"Alice's final key (agreed): {alice_final_key}")
    print(f"Bob's final key (received):   {bob_final_key}")

    if alice_final_key == bob_final_key and alice_final_key:
        print("Key exchange successful (based on conclusive measurements).")
    elif not alice_final_key:
        print("Key exchange failed (no conclusive measurements).")
    else:
        print("Potential errors or inconclusive measurements.")