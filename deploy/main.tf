# Terraform configuration for Alibaba Cloud Infrastructure
# Orchestrates Container Registry (ACR) and ECS Instance to host AegisOps

terraform {
  required_providers {
    alicloud = {
      source  = "aliyun/alicloud"
      version = "~> 1.210.0"
    }
  }
}

variable "region" {
  type        = string
  default     = "ap-southeast-1" # Singapore region (international workspace)
  description = "The Alibaba Cloud region to deploy resources in."
}

variable "ecs_instance_type" {
  type        = string
  default     = "ecs.t6-c1m2.large" # 2 vCPU, 4GB RAM Burstable type
  description = "ECS instance type for the orchestrator host."
}

variable "acr_namespace" {
  type        = string
  default     = "aegisops-registry"
  description = "Alibaba Cloud Container Registry namespace."
}

provider "alicloud" {
  region = var.region
}

# 1. Network Configuration (VPC and VSwitch)
resource "alicloud_vpc" "vpc" {
  vpc_name   = "aegisops-vpc"
  cidr_block = "10.0.0.0/16"
}

resource "alicloud_vswitch" "vswitch" {
  vswitch_name = "aegisops-vswitch"
  vpc_id       = alicloud_vpc.vpc.id
  cidr_block   = "10.0.1.0/24"
  zone_id      = "${var.region}-a"
}

# 2. Security Group Configuration
resource "alicloud_security_group" "sg" {
  name        = "aegisops-sg"
  description = "AegisOps Security Group rules"
  vpc_id      = alicloud_vpc.vpc.id
}

# Ingress SSH
resource "alicloud_security_group_rule" "allow_ssh" {
  type              = "ingress"
  ip_protocol       = "tcp"
  nic_type          = "intranet"
  policy            = "accept"
  port_range        = "22/22"
  priority          = 1
  security_group_id = alicloud_security_group.sg.id
  cidr_ip           = "0.0.0.0/0"
}

# Ingress Dashboard/Web Port
resource "alicloud_security_group_rule" "allow_web" {
  type              = "ingress"
  ip_protocol       = "tcp"
  nic_type          = "intranet"
  policy            = "accept"
  port_range        = "80/80"
  priority          = 1
  security_group_id = alicloud_security_group.sg.id
  cidr_ip           = "0.0.0.0/0"
}

# 3. Alibaba Cloud Container Registry (ACR) Repository
resource "alicloud_cr_namespace" "acr_ns" {
  name        = var.acr_namespace
  auto_create = true
  default_visibility = "PUBLIC"
}

resource "alicloud_cr_repo" "acr_repo" {
  namespace = alicloud_cr_namespace.acr_ns.name
  name      = "aegisops-sandbox"
  summary   = "AegisOps secure container sandbox image registry"
  repo_type = "PUBLIC"
}

# 4. Elastic Compute Service (ECS) Instance
resource "alicloud_instance" "orchestrator" {
  availability_zone    = "${var.region}-a"
  instance_name        = "aegisops-orchestrator"
  image_id             = "ubuntu_22_04_x64_20G_alibase_20230613.vhd" # Ubuntu LTS
  instance_type        = var.ecs_instance_type
  security_groups      = [alicloud_security_group.sg.id]
  vswitch_id           = alicloud_vswitch.vswitch.id
  internet_max_bandwidth_out = 5 # Assigns a public IP address

  # Provision Docker and Git tools on startup
  user_data = <<-EOF
              #!/bin/bash
              apt-get update
              apt-get install -y docker.io git python3-pip python3-venv
              systemctl start docker
              systemctl enable docker
              EOF
}

output "ecs_public_ip" {
  value       = alicloud_instance.orchestrator.public_ip
  description = "The public IP address of the AegisOps orchestrator instance."
}

output "acr_repo_url" {
  value       = "registry.${var.region}.aliyuncs.com/${var.acr_namespace}/aegisops-sandbox"
  description = "The push registry URL for the secure sandbox image."
}
