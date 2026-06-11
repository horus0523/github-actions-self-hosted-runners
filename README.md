# GitHub Actions Self-Hosted Runners

```
DIAGRAM: GITHUB ACTIONS – WORKFLOW & RUNNER ARCHITECTURE

                        +--------------------+
                        |  Trigger: Push/PR  |
                        +--------------------+
                                 |
                                 v
+-------------------+     +------------------------+
|                   | --> |   Checkout Code        |
|  GITHUB ACTIONS   | --> |   Setup Python Matrix  |
|   WORKFLOW        | --> |   Install Dependencies |
|                   | --> |   Lint with flake8     |
+-------------------+ --> |   Run Tests            |
                          |   Docker Login         |
                          |   Build & Push Image   |
                          +------------------------+
                                 |
                                 v
                      +-------------------------+
                      | Where does it run?      |
                      +-----------+-------------+
                                  |
             +--------------------+--------------------+
             |                                         |
             v                                         v
 +-----------------------------+          +-----------------------------+
 |  PART A: GITHUB RUNNERS     |          |  PART B: SELF-HOSTED        |
 |  (Managed Infrastructure)   |          |  (Custom AWS EC2)           |
 +-----------------------------+          +-----------------------------+
 | * GitHub Runners            |          | * EC2 Instance              |
 | * Auto-scaled VMs           |          | * Security Group            |
 | * No infrastructure config  |          | * Key Pair                  |
 +-----------------------------+          +-----------------------------+
```

## Description

This repository publishes an active GitHub-hosted CI workflow plus reusable
workflow and Terraform examples for an EC2-based self-hosted runner. Treat the
checked-in workflows and the `templates/` directory differently:

- **Active workflows** under `.github/workflows/` are the workflows GitHub can run
  from this repository.
- **Templates** under `templates/` are examples for operators to copy and adapt;
  they are not executed by this repository until moved into `.github/workflows/`.

The documentation is organized in two parts:

- **Part A**: Basic implementation with GitHub-hosted runners
- **Part B**: Advanced configuration with self-hosted runners on AWS EC2

The active CI path runs Python linting, tests, and a container build/push from
GitHub-hosted runners. Self-hosted runner usage is documented as an operator
controlled path with explicit infrastructure and trust boundaries.

## Active Workflows vs Templates

| Path | Status | Purpose |
|------|--------|---------|
| `.github/workflows/test_and_build.yaml` | Active workflow | Runs CI on GitHub-hosted runners for pushes and pull requests to `main`. |
| `.github/workflows/reusable-ci-pipeline.yml` | Reusable workflow | Reusable CI workflow for trusted self-hosted runner usage. |
| `.github/workflows/reusable-runner-provision.yml` | Reusable workflow | Reusable Terraform plan/apply workflow for trusted callers. |
| `templates/test_and_build-part-a.yaml` | Example only | GitHub-hosted runner template. |
| `templates/test_and_build-part-b.yaml` | Example only | Self-hosted runner template that assumes an already hardened runner host. |

The active checked-in workflow uses explicitly tracked workflow permissions.
The reusable provisioning workflow in this repository also declares its required
permissions and only runs when another workflow calls it.

## Tech Stack

- **Python** (3.11, 3.12) - Development and testing
- **GitHub Actions** - Automated CI/CD pipeline
- **AWS EC2** - Infrastructure for custom runners
- **AWS CLI** - Cloud resource management
- **Docker** - Application containerization
- **pytest** - Testing framework
- **flake8** - Static code analysis
- **GitHub Container Registry** - Image registry

## Pipeline Flow

```
COMPLETE CI/CD PIPELINE FLOW

    Push/PR Event
         |
         v
    +----------+     +-------------+     +----------+     +----------+
    | Checkout | --> | Setup Multi | --> | Lint &   | --> | Docker   |
    | Source   |     | Python Env  |     | Test     |     | Deploy   |
    +----------+     +-------------+     +----------+     +----------+
```

## Project Structure

```
├── .github/
│   ├── terraform/                   # Terraform for EC2 runner provisioning
│   │   └── runner-ec2/              # Terraform for EC2 runner provisioning
│   │       ├── main.tf              # EC2 instance resource
│   │       ├── variables.tf         # Input variables
│   │       ├── outputs.tf           # Output values
│   │       ├── sg.tf                # Security group rules
│   │       └── iam.tf               # IAM role, attached policy, and trust relationship
│   └── workflows/
│       ├── test_and_build.yaml      # Main CI/CD pipeline
│       ├── reusable-runner-provision.yml  # Reusable Terraform provisioning workflow
│       └── reusable-ci-pipeline.yml       # Reusable CI workflow for self-hosted runners
├── src/                            # Application source code
│   ├── main.py                     # Main file
│   └── test.py                     # Unit tests
├── templates/                      # Example workflows; not active until copied
├── requirements.txt                # Python dependencies
├── Dockerfile                      # Container configuration
├── README.md                       # README file
└── .gitignore                      # Git ignore file
```

## Active Pipeline Configuration

### Triggers

- Push to main branch
- Pull Requests to main branch

### Matrix Strategy

The pipeline runs on multiple Python versions:

- Python 3.11
- Python 3.12

### Pipeline Steps

1. **Checkout Repository**

   - Downloads the source code

2. **Setup Python**

   - Configures Python environment using matrix strategy

3. **Install Dependencies**

   ```bash
   python -m pip install --upgrade pip
   pip install flake8 pytest
   pip install -r requirements.txt
   ```

4. **Lint with flake8**

   - Verifies syntax and code style
   - Configuration: max-complexity=10, max-line-length=127

5. **Run Tests**

   ```bash
   python -m pytest src/test.py
   ```

6. **Container Build**
   - Pull requests build the image without publishing it
   - Pushes to `main` build and publish the image to GitHub Container Registry

---

## PART A: GitHub Hosted Runners

---

### Initial Setup

#### 1. **Configure Your Repository**

```bash
# Create your own repository based on this project
git clone https://github.com/horus0523/github-actions-self-hosted-runners.git
cd github-actions-self-hosted-runners

# Configure your remote repository (modify with your data)
git remote set-url origin https://github.com/YOUR-USERNAME/YOUR-REPOSITORY.git
```

#### 2. **Verify Local Dependencies**

##### Create virtual environment

```bash
# Create a virtual environment called "venv"
python -m venv venv
```

##### Activate it (according to your operating system)

```bash
# On Linux/macOS:
source venv/bin/activate
```

```bash
# On Windows (CMD):
venv\Scripts\activate
```

```bash
# On PowerShell:
venv\Scripts\Activate.ps1
```

```bash
# Install Python dependencies
pip install -r requirements.txt
```

#### Run tests to verify everything works

```bash
# Run tests to verify everything works
python -m pytest src/test.py -v
```

```bash
# Verify code quality with flake8
flake8 src/ --max-line-length=127 --exclude=__pycache__
```

```bash
# Run the main application
python src/main.py
```

#### 3. **Enable GitHub Actions**

- Go to your repository on GitHub
- Navigate: `Settings > Actions > General`
- Enable: `Allow all actions and reusable workflows`

### Pipeline Operation

The `test_and_build.yaml` workflow automatically executes:

1. **Code Quality Check**

   ```bash
   # Change directory to src/ and run flake8
   cd src
   flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
   flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
   ```

2. **Multi-Version Testing**

   - Runs tests on Python 3.11 and 3.12
   - Matrix strategy for compatibility

3. **Container Build**
   - Pull requests validate the Docker build without pushing
   - Pushes to `main` publish the image to GitHub Container Registry

### Monitoring and Debugging

```bash
# View pipeline run list
gh run list
```

```bash
# View workflow execution logs
gh run view RUN-ID --log # Replace RUN-ID with one from the list
```

```bash
# list all available workflows
gh workflow list
```

```bash
# Show detailed information of a specific workflow
gh workflow view test_and_build.yaml
```

---

## PART B: Self-Hosted Runners on AWS EC2

This section describes the self-hosted runner operating model. The workflow and
template examples assume trusted branches and trusted callers. Do not run
self-hosted workflows for pull requests from untrusted forks.

---

### Configure Variables in GitHub

#### Required Variables

1. `${{ vars.DOCKERHUB_USERNAME }}` → your **Docker Hub username**
2. `${{ secrets.DOCKERHUB_TOKEN }}` → an **access token** generated in Docker Hub

#### Step 1: Create a token in Docker Hub

1. Go to [https://hub.docker.com/](https://hub.docker.com/) and **sign in**
2. Click on your user icon (top right) → choose **"Account Settings"**
3. In the sidebar menu, select **"Security"**.
4. In the **"Access Tokens"** section, click **"New Access Token"**
5. Give it a name (e.g., `github-token`), and give it default permissions
6. Click **"Create"**
7. Copy the generated token (it's only shown once!)

#### Step 2: Go to your repository on GitHub

1. Go to your repository on GitHub
2. Click on the **"Settings"** tab
3. In the sidebar menu, scroll down to **"Secrets and variables"** → choose **"Actions"**

#### Step 3: Add the **secret**

1. Click on **"New repository secret"**
2. Fill in the fields as follows:

   - **Name:** `DOCKERHUB_TOKEN`
   - **Value:** paste the token you copied from Docker Hub

3. Click **"Add secret"**

#### Step 4: Add the **variable**

1. From the same menu (**"Secrets and variables" → "Actions"**), go to the **"Variables"** tab
2. Click on **"New repository variable"**
3. Fill in the fields as follows:

   - **Name:** `DOCKERHUB_USERNAME`
   - **Value:** your Docker Hub username (e.g., `horuschourio`)

4. Click **"Add variable"**

### AWS Environment Setup

#### 1. **Configure AWS CLI**

```bash
# Install AWS CLI v2
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip && sudo ./aws/install
```

```bash
# Configure credentials
aws configure
# AWS Access Key ID: [Your Access Key]
# AWS Secret Access Key: [Your Secret Key]
# Default region: us-east-1
# Default output format: json
```

### 2. **Create AWS Infrastructure**

#### 2.1 Sign in to AWS

1. Go to [https://aws.amazon.com/console/](https://aws.amazon.com/console/)
2. Sign in with your account

   - If you have an IAM user, **use it instead of the root account** for security

#### 2.2 Choose the Right Region

Make sure to select the region where you will create all resources:

- **US East (N. Virginia)** - `us-east-1`: Most commonly used with lower prices.
- **South America (São Paulo)** - `sa-east-1`: Better latency if you are in South America.

#### 2.3 Create Required Resources Before the Instance

##### 1. Create the key pair (SSH key)

This key is necessary to connect to the server. It can only be downloaded once.

1. Search for **EC2** in the search bar and access the service
2. In the left menu, go to **Key Pairs** (under "Network & Security")
3. Click on **Create key pair**:

   - **Name**: `github-runner-key-pair`
   - **Type**: ED25519
   - **Format**:

   - `.pem` for Linux, macOS, or Windows with WSL
   - `.ppk` for PuTTY on Windows

4. Click on **Create key pair**

A `.pem` or `.ppk` file will be downloaded. **Save it carefully**. It's essential for connecting.

##### 2. Create a Security Group

This allows you to define what traffic can access your instance.

1. In the left menu, go to **Security Groups**

2. Click on **Create security group**

3. Configure as follows:

   - **Name**: `ssh-from-my-ip`
   - **Description**: `Allow SSH access only from my IP`
   - **VPC**: Leave the default

4. In **Inbound rules**, click "Add rule":

5. **Add rule:**

   - Type: SSH
   - Port: 22
   - Source type: My IP

6. In **Outbound rules (verify they are present):**

- Prefer **DNS resolvers only** on port 53 and **approved HTTPS destinations only** on port 443.
- Enable **HTTP/80 only** when a bootstrap mirror cannot use HTTPS, and scope it to explicit CIDRs.
- Do **not** keep a blanket `0.0.0.0/0` default just because it is convenient.

7. Click **Create security group**

#### 2.4 Create the EC2 Instance

##### 1. Launch new instance

1. Go to **Instances** > **Launch instances**
2. Set a name like: `github-runner-ec2`

##### 2. Choose operating system

Choose a **Free tier eligible** AMI, such as:

- **Ubuntu Server 24.04 LTS**

##### 3. Select instance type

- Use **t2.micro** or **t3.micro**, both within the free tier.

##### 4. Choose key pair

- In **Key pair (login)**, choose:

  - **Choose existing key pair**
  - Select `github-runner-key-pair`

**Make sure you have the `.pem` or `.ppk` file saved**, or you won't be able to connect.

##### 5. Configure network and security

- **VPC and subnet**: Leave the default values
- **Auto-assign public IP**: Enabled
- **Firewall (Security group)**:

- Select **"Select existing security group"**
- Check the `ssh-from-my-ip` group you created earlier

##### 6. Additional configuration

- **Storage**: Leave the default 8 GB (free)
- **Tags (optional)**:

  - Key: `Name`, Value: `github-runner-ec2`

Click **Launch instance**

##### 7. Wait and get IP

1. Go to **Instances** > **View all instances**
2. Wait for the status to be **Running** and the checks to be **2/2 passed**
3. Copy the **Public IPv4 address**

#### 2.5 Connect to the instance

##### From Linux, macOS or Windows with WSL

1. Open the terminal
2. Go to the directory where you saved your `.pem` file
3. Set permissions:

   ```bash
   chmod 400 github-runner-key-pair.pem
   ```

4. Connect:

   ```bash
   ssh -i "github-runner-key-pair.pem" ubuntu@YOUR_PUBLIC_IP
   ```

### 3. Configure the runner

3.1 **Go to: GitHub Repo > Settings > Actions > Runners**

3.2 **Click "New self-hosted runner"**

3.3 **Follow the instructions for your OS (in this case the EC2 instance)**

3.4 **Follow the step-by-step instructions (example command below)**

```bash
# 1. Create a folder for the runner
mkdir actions-runner && cd actions-runner

# 2. Download the package (adjust URL according to version)
curl -o actions-runner-linux-x64-2.315.0.tar.gz -L https://github.com/actions/runner/releases/download/v2.315.0/actions-runner-linux-x64-2.315.0.tar.gz

# 3. Extract the files
tar xzf ./actions-runner-linux-x64-2.315.0.tar.gz

# 4. Configure your repository (customized for your repo and token)
./config.sh --url https://github.com/YOUR_USERNAME/YOUR_REPOSITORY --token YOUR_TOKEN

# 5. Follow the instructions and respond when prompted for the runner name and group, or just press 'enter' to accept the default options

# You will see these questions:
# Enter the name of the runner group [default: Default]:
# Enter the name of runner [default: ip-172-31-xx-xx]: MY-CUSTOM-RUNNER
# Enter any additional labels []:
# Enter name of work folder [default: _work]:
```

3.5 **Options for the name:**

- **Accept default**: Use the private IP of the EC2 instance
- **Custom**: Write something descriptive like `aws-ec2-runner-prod`
- **Function-based**: `github-runner-testing`, `ci-cd-runner`

### 4. Start the runner

```bash
./run.sh # Run it manually
```

This will start the runner in interactive mode (open terminal). To leave it running as a service:

```bash
# To install/manage as a Linux service
sudo ./svc.sh install
sudo ./svc.sh start
```

Check the service status

```bash
sudo systemctl status actions.runner.*
```

### 5. Verify that it's active

Go back to your GitHub repository → **Settings > Actions > Runners**

You should see your new runner as `online`.

### 6. **Use the self-hosted workflow template only after host hardening**

`templates/test_and_build-part-b.yaml` is an example for a trusted self-hosted
runner. Copy it into `.github/workflows/` only after the runner host, IAM role,
and security group are configured for your environment.

Keep it manual by default unless you have an explicit trusted-branch operating
model for that runner.

```yaml
name: Python Application CI-CD

on:
  workflow_dispatch:

permissions:
  contents: read
  packages: write

jobs:
  test_and_build:
    runs-on: self-hosted

    strategy:
      matrix:
        python-version: ["3.11", "3.12"]

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          persist-credentials: false

      - name: Setup Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install flake8 pytest
          if [ -f requirements.txt ]; then pip install -r requirements.txt; fi

      - name: Install and setup Docker
        run: |
          sudo apt update
          sudo apt install docker.io -y
          sudo systemctl start docker
          sudo systemctl enable docker

      - name: Verify Docker setup
        run: |
          docker --version
          docker info

      # Do not relax /var/run/docker.sock permissions in workflow steps. Grant
      # runner access during host provisioning, then keep the socket restricted.

      - name: Lint with flake8
        working-directory: src
        run: |
          # Fail if there are serious syntax errors or undefined names
          flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
          # Warnings for the rest of the issues
          flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

      - name: Run tests with pytest
        working-directory: src
        run: |
          python -m pytest test.py

      - name: Login to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ vars.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}

      - name: Set up QEMU
        uses: docker/setup-qemu-action@v3

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Build and push
        uses: docker/build-push-action@v6
        with:
          context: .
          push: true
          tags: ${{ vars.DOCKERHUB_USERNAME }}/mi-app-test:latest
```

### 7. Permissions and Security

The example workflow uses the following permissions:

- `contents: read` - Code reading
- `packages: write` - Write access to GitHub Container Registry

Do not grant broader workflow permissions unless a job explicitly needs them.

### 8. Repository Secrets Configuration

The workflow uses:

- `GITHUB_TOKEN` (automatic)
- `Docker`:
  - username: ${{ vars.DOCKERHUB_USERNAME }}
  - password: ${{ secrets.DOCKERHUB_TOKEN }}

#### Security Group Rules:

1. **Inbound rules**

   - Type: SSH
   - Port: 22
   - Source type: My IP

2. **Outbound rules**

- Type: DNS / HTTPS only by default
- Port: 53 (TCP/UDP) and 443 (TCP)
- Destination: your explicit resolver and approved HTTPS CIDRs
- Optional: add port 80 only for a documented bootstrap mirror that cannot use HTTPS

---

### Runner Management

```bash
# Check runner status
sudo systemctl status actions.runner.*

# View logs in real time
sudo journalctl -u actions.runner.* -f

# Restart runner if necessary
sudo systemctl restart actions.runner.*
```

```bash
# List all GitHub Actions runner services
sudo systemctl list-units --type=service | grep actions.runner

# Or view services that contain "runner"
sudo systemctl list-units --type=service | grep runner
```

---

## Runner-as-Code: Terraform Provisioning

### Overview

The Terraform files under `.github/terraform/runner-ec2/` are the source of
truth for host-level access controls used by the reusable provisioning workflow:

- `.github/terraform/runner-ec2/main.tf` attaches the IAM instance profile and
  security group to the EC2 instance.
- `.github/terraform/runner-ec2/iam.tf` defines the instance role and profile.
- `.github/terraform/runner-ec2/sg.tf` scopes inbound SSH, Docker TLS, DNS,
  HTTPS, and optional bootstrap HTTP rules.

The values `instance_id`, `public_ip`, and `security_group_id` are Terraform
outputs declared in `.github/terraform/runner-ec2/outputs.tf`. The reusable
workflow does not publish them back to the caller as workflow outputs.

Workflow examples must not compensate for host misconfiguration by changing
Docker socket permissions at runtime.

### Architecture

The diagram below reflects the committed reusable workflow and Terraform layout.

```
┌─────────────────────────────────────────────────────────────────┐
│                    GitHub Repository                             │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  Trusted caller workflow                                    │  │
│  └──────────────────────────┬───────────────────────────────┘  │
│                               │ workflow_call                   │
│                               v                                 │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  reusable-runner-provision.yml (called workflow)           │  │
│  │  ├─ Configure AWS credentials                              │  │
│  │  ├─ terraform init → validate → plan                        │  │
│  │  ├─ apply path runs when caller sets with.apply: true       │  │
│  │  └─ no workflow outputs published to caller                 │  │
│  └──────────────────────────┬───────────────────────────────┘  │
│                               │                                 │
│                               v                                 │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  AWS EC2 Instance (GitHub Runner)                           │  │
│  │  ├─ IAM Instance Profile (tracked policy + trust policy)    │  │
│  │  ├─ Security Group (SSH, Docker TLS, DNS, HTTPS, optional   │  │
│  │  │  bootstrap HTTP egress)                                  │  │
│  │  └─ Tags: ManagedBy=terraform                              │  │
│  └────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Terraform Structure

```
.github/terraform/runner-ec2/
├── main.tf         # EC2 instance resource
├── variables.tf    # Environment, AMI, instance type, CIDR
├── outputs.tf      # Terraform outputs: instance_id, public_ip, security_group_id
├── sg.tf          # Security group with scoped ingress and egress rules
└── iam.tf         # IAM role + instance profile
```

### Provision a Runner

1. **Call the reusable workflow** from a trusted repository or wrapper workflow:

 ```yaml
 jobs:
   provision-runner:
      uses: owner/repo/.github/workflows/reusable-runner-provision.yml@main
      with:
        environment: dev
        apply: false
        terraform_source_repository: horus0523/github-actions-self-hosted-runners
        terraform_source_ref: main
        tfvars_file: .github/terraform/runner-ec2/dev.tfvars
      secrets:
        AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
        AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
 ```

This `workflow_call` entrypoint always runs Terraform init, validate, and plan.
`Terraform Apply` runs only when the trusted caller sets `with.apply: true`.
Keep the default `false` for review and validation flows. By default, the
workflow checks out `horus0523/github-actions-self-hosted-runners@main` so the
Terraform source is explicit and the `.github/terraform/runner-ec2` directory is
always available. Override `terraform_source_repository` or
`terraform_source_ref` only when you intentionally want to provision from a fork
or another revision.

2. **Provide a tfvars file**. Callers must pass `with.tfvars_file` and point it
   at a file that exists inside the checked-out Terraform source repository/ref.
   The reusable workflow always runs `terraform plan -var-file=...`, so the
   caller-owned tfvars file must provide required values such as `ami` and
   `subnet_id`. This repository does not commit a default `<environment>.tfvars`
   file for you. Example caller-owned `dev.tfvars`:

```hcl
ami                         = "ami-0abcdef1234567890"
instance_type               = "t3.micro"
subnet_id                   = "subnet-0123456789abcdef0"
environment                 = "dev"
allowed_ssh_cidr            = ["203.0.113.10/32"]
docker_daemon_allowed_cidr  = ["203.0.113.10/32"]
runner_dns_egress_cidr_blocks   = ["192.0.2.53/32"]
runner_https_egress_cidr_blocks = ["198.51.100.0/24"]
allow_bootstrap_http_egress     = false
bootstrap_http_egress_cidr_blocks = ["198.51.100.80/32"]
```

> `203.0.113.10/32`, `192.0.2.53/32`, `198.51.100.0/24`, and `198.51.100.80/32` are TEST-NET placeholders only. Replace them with your real admin, DNS, HTTPS, and optional HTTP mirror CIDRs before `terraform apply`.

### IAM Policy and Trust Relationship

The tracked Terraform for the runner IAM role looks up an IAM policy by the
configured name `GitHubActionsRunner managed policy` and attaches the returned
ARN to the role. It also uses the following EC2 trust relationship:

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Action": "sts:AssumeRole",
    "Effect": "Allow",
    "Principal": { "Service": "ec2.amazonaws.com" }
  }]
}
```

### Security Group Rules

| Direction | Port | Protocol | Source | Purpose |
|-----------|------|----------|--------|---------|
| Inbound | 22 | TCP | Admin CIDR | SSH access |
| Inbound | 2376 | TCP | `docker_daemon_allowed_cidr` | Docker daemon TLS |
| Outbound | 53 | TCP/UDP | `runner_dns_egress_cidr_blocks` | DNS |
| Outbound | 443 | TCP | `runner_https_egress_cidr_blocks` | GitHub, registries, HTTPS APIs |
| Outbound | 80 | TCP | `bootstrap_http_egress_cidr_blocks` | Optional bootstrap HTTP mirrors only when `allow_bootstrap_http_egress = true` |

Operational notes:

- The runner explicitly attaches the Terraform-managed security group.
- The tracked defaults do not leave `0.0.0.0/0` open. The README values are
  placeholders so you must define approved DNS resolvers and HTTPS destinations.
- If you need broader egress, define it explicitly in your `tfvars` instead of
  inheriting broad CIDRs from the repository.
- Set `allow_bootstrap_http_egress = true` only when a required mirror does not
  support HTTPS, and document the reason in your fork or ADR.
- Do not run self-hosted workflows for pull requests from untrusted forks. This
  repository keeps them as operator-controlled examples.

## Comparison: GitHub vs Self-Hosted

| Aspect               | GitHub Hosted    | Self-Hosted (AWS)   | Explanation                                                                                                                        |
| -------------------- | ---------------- | ------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| **Setup Time**       | Immediate        | Manual registration | GitHub Hosted runners are ready instantly. Self-hosted requires launching a server, installing the runner, and following the manual registration steps. |
| **Cost**             | Included minutes | Pay-per-use AWS     | GitHub provides free minutes (especially for public repos). With AWS, you pay for compute, storage, and network use.               |
| **Control**         | Limited          | Total               | GitHub Hosted has a fixed environment. Self-hosted gives full control over OS, installed tools, and network settings.              |
| **Customization**    | Basic            | Complete            | GitHub runners allow basic customization inside the job. Self-hosted runners can be customized at system level.                    |
| **Security**         | GitHub managed   | Your responsibility | GitHub secures their infrastructure. With self-hosted, you're responsible for updates, firewalls, access control, etc.             |
| **Scalability**      | Auto             | Manual              | GitHub automatically scales runners for parallel jobs. With self-hosted, you need to configure scaling or provision more machines. |

---

## Clean Up Resources When Finished

### 1. Terminate the instance

1. Go to **Instances**
2. Select yours
3. Click on **Instance state** > **Terminate instance**

### 2. Delete the security group

Once the instance disappears:

1. Go to **Security Groups**
2. Select `ssh-from-my-ip`
3. Click on **Actions** > **Delete security group**

### 3. Delete the key pair

1. Go to **Key Pairs**
2. Select `github-runner-key-pair`
3. Click on **Actions** > **Delete**
4. Delete the `.pem` or `.ppk` file from your computer if you no longer need it

## Verify cleanup

```bash
# Verify no instances are still running
aws ec2 describe-instances --region us-east-1 --query 'Reservations[].Instances[?State.Name==`running`]'

# Verify security groups (should not show the one you created)
aws ec2 describe-security-groups --region us-east-1 --query 'SecurityGroups[?GroupName==`ssh-from-my-ip`]'

# Verify key pairs (should not show the one you created)
aws ec2 describe-key-pairs --region us-east-1 --query 'KeyPairs[?KeyName==`github-runner-key-pair`]'
```

---

## Troubleshooting

### Common Issues

#### **Runner not showing up in GitHub**

```bash
# Verify connection
curl -I https://api.github.com

# Review configuration
cat actions-runner/.runner
```

#### **Pipeline failures**

```bash
# View detailed logs
sudo journalctl -u actions.runner.github-runner --since "1 hour ago"

# Verify resources
free -h && df -h
```

#### **Permission issues**

```bash
# Assign ownership of the runner directory to the 'ubuntu' user
sudo chown -R ubuntu:ubuntu ~/actions-runner

# Make the runner start script executable
sudo chmod +x actions-runner/run.sh
```

## Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Documentation](https://docs.docker.com/)
- [Python Testing with pytest](https://docs.pytest.org/)
- [Flake8 Documentation](https://flake8.pycqa.org/)
