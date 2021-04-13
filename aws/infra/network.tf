data "aws_region" "current" {}


data "aws_availability_zones" "available" {
  state = "available"
  filter {
    name   = "region-name"
    values = [data.aws_region.current.name]
  }
}


locals {
  nb_az = length(data.aws_availability_zones.available.names)
}


resource "aws_vpc" "sec" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true

  tags = {
    Name    = var.tag_project_name
    project = var.tag_project_name
  }
}


resource "aws_security_group" "sec" {
  name   = var.tag_project_name
  vpc_id = aws_vpc.sec.id

  ingress {
    from_port   = 3306
    to_port     = 3306
    protocol    = "tcp"
    cidr_blocks = [var.self_ip]
  }

  ingress {
    from_port = 0
    to_port   = 0
    protocol  = "-1"
    self      = true
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name    = var.tag_project_name
    project = var.tag_project_name
  }
}


resource "aws_internet_gateway" "sec" {
  vpc_id = aws_vpc.sec.id

  tags = {
    Name    = var.tag_project_name
    project = var.tag_project_name
  }
}


resource "aws_route_table" "sec" {
  vpc_id = aws_vpc.sec.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.sec.id
  }

  tags = {
    Name    = var.tag_project_name
    project = var.tag_project_name
  }
}


resource "aws_subnet" "sec" {
  count = local.nb_az

  vpc_id            = aws_vpc.sec.id
  cidr_block        = "10.0.${count.index + 1}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = {
    Name    = "${var.tag_project_name}_${data.aws_availability_zones.available.names[count.index]}"
    project = var.tag_project_name
  }
}


resource "aws_route_table_association" "sec" {
  count = local.nb_az

  subnet_id      = aws_subnet.sec[count.index].id
  route_table_id = aws_route_table.sec.id
}


resource "aws_db_subnet_group" "sec" {
  name       = "${var.tag_project_name}_rds"
  subnet_ids = aws_subnet.sec[*].id

  tags = {
    Name    = "${var.tag_project_name}_rds"
    project = var.tag_project_name
  }
}
