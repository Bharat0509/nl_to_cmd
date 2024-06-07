from flask import Flask, request, jsonify
from ctransformers import AutoModelForCausalLM, AutoTokenizer
import paramiko

# Initialize the model
print("Loading model...")
model_path = "./mistral_llm_v3_q4_K_M.gguf"
llm = AutoModelForCausalLM.from_pretrained(model_path)
print("Model loaded successfully!")

alpaca_prompt = """Below is an instruction that describes a task, paired with an input that provides further context. Write a nxos command in response that appropriately completes the request.

### Instruction:
{}

### Input:
{}

### Response:
{}"""

app = Flask(__name__)

# SSH connection parameters
SSH_HOST = '10.127.124.68'
SSH_USERNAME = 'admin'
SSH_PASSWORD = 'nbv_12345'

# SSH client setup
ssh_client = paramiko.SSHClient()
ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

# Establish SSH connection
ssh_client.connect(hostname=SSH_HOST,username=SSH_USERNAME, password=SSH_PASSWORD)

@app.route('/health', methods=['GET'])
def health_check():
    print("Health check requested.")
    return jsonify({'status': 'healthy'})

@app.route('/generate', methods=['POST'])
def generate_response():
    data = request.json
    instruction = data.get('instruction')
    input_context = data.get('input', "")

    # Format the prompt
    prompt = alpaca_prompt.format(instruction, input_context, "")
    print(f"Received instruction: {instruction}")
    if input_context:
        print(f"Received input context: {input_context}")

    # Generate output
    output = llm.__call__(prompt=prompt, max_new_tokens=128)
    
    # Extract the generated text
    generated_text = output.strip()
    print(f"Generated response: {generated_text}")

    # Execute command on switch
    stdin, stdout, stderr = ssh_client.exec_command(generated_text + " !") 
    command_output = stdout.read().decode('utf-8')
    print(f"Command output: {command_output}")
   
    command_output=f"{generated_text} \r\nExecuting... \r\n\n{command_output}"
    return jsonify({'response': command_output})

if __name__ == '__main__':
    print("Starting Flask server...")
    app.run(debug=True)

