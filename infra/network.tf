resource "aws_vpc" "sec_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true

  tags = {
    Name    = "${var.tag_project_name} VPC"
    project = var.tag_project_name
  }
}

resource "aws_security_group" "sec_sg" {
  name   = "sec_security_group"
  vpc_id = aws_vpc.sec_vpc.id

  ingress {
    from_port   = 3306
    to_port     = 3306
    protocol    = "tcp"
    cidr_blocks = ["91.165.221.21/32"]
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
    Name    = "${var.tag_project_name} security group"
    project = var.tag_project_name
  }
}

resource "aws_internet_gateway" "sec_igw" {
  vpc_id = aws_vpc.sec_vpc.id

  tags = {
    Name    = "${var.tag_project_name} internet gateway"
    project = var.tag_project_name
  }
}

resource "aws_route_table" "sec_rt" {
  vpc_id = aws_vpc.sec_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.sec_igw.id
  }

  tags = {
    Name    = "${var.tag_project_name} route table"
    project = var.tag_project_name
  }
}

resource "aws_subnet" "sec_sn_a" {
  vpc_id            = aws_vpc.sec_vpc.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "eu-west-3a"

  tags = {
    Name    = "${var.tag_project_name} subnet A"
    project = var.tag_project_name
  }
}

resource "aws_subnet" "sec_sn_b" {
  vpc_id            = aws_vpc.sec_vpc.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = "eu-west-3b"

  tags = {
    Name    = "${var.tag_project_name} subnet B"
    project = var.tag_project_name
  }
}

resource "aws_subnet" "sec_sn_c" {
  vpc_id            = aws_vpc.sec_vpc.id
  cidr_block        = "10.0.3.0/24"
  availability_zone = "eu-west-3c"

  tags = {
    Name    = "${var.tag_project_name} subnet C"
    project = var.tag_project_name
  }
}

resource "aws_route_table_association" "a" {
  subnet_id      = aws_subnet.sec_sn_a.id
  route_table_id = aws_route_table.sec_rt.id
}

resource "aws_route_table_association" "b" {
  subnet_id      = aws_subnet.sec_sn_b.id
  route_table_id = aws_route_table.sec_rt.id
}

resource "aws_route_table_association" "c" {
  subnet_id      = aws_subnet.sec_sn_c.id
  route_table_id = aws_route_table.sec_rt.id
}

resource "aws_db_subnet_group" "sec_db_sng" {
  name = "sec_rds_subnet_group"
  subnet_ids = [
    aws_subnet.sec_sn_a.id,
    aws_subnet.sec_sn_b.id,
    aws_subnet.sec_sn_c.id
  ]

  tags = {
    Name    = "${var.tag_project_name} RDS subnet group"
    project = var.tag_project_name
  }
}
