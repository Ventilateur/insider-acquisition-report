resource "aws_db_instance" "sec_db_instance" {
  allocated_storage      = 20
  apply_immediately      = true
  db_subnet_group_name   = aws_db_subnet_group.sec_db_sng.name
  engine                 = "mysql"
  engine_version         = "8.0"
  identifier             = "${lower(var.tag_project_name)}-db"
  instance_class         = "db.t2.micro"
  multi_az               = false
  name                   = var.tag_project_name
  username               = var.db_username
  password               = var.db_password
  publicly_accessible    = true
  skip_final_snapshot    = true
  vpc_security_group_ids = [aws_security_group.sec_sg.id]

  tags = {
    Name    = "${var.tag_project_name} database"
    project = var.tag_project_name
  }
}


resource "null_resource" "db_setup" {
  depends_on = [
    aws_db_instance.sec_db_instance,
    aws_db_subnet_group.sec_db_sng
  ]

  provisioner "local-exec" {
    command = "docker run --rm -i mysql mysql -u${var.db_username} -p${var.db_password} -h ${aws_db_instance.sec_db_instance.address} ${aws_db_instance.sec_db_instance.name} < sql/initialize.sql"
  }
}


resource "aws_dynamodb_table" "sec4_states" {
  hash_key = "State"
  name = "SEC4States"
  read_capacity  = 1
  write_capacity = 1

  attribute {
    name = "State"
    type = "S"
  }

  tags = {
    Name    = "${var.tag_project_name} states"
    project = var.tag_project_name
  }
}
