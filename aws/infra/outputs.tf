output "network" {
  value = {
    security_group_id = aws_security_group.sec.id
    subnet_ids        = aws_subnet.sec[*].id
  }
}

output "db" {
  value = {
    host = aws_db_instance.sec.address
    name = aws_db_instance.sec.name
    event_names = {
      db_started = aws_cloudwatch_event_rule.db_started.name
    }
  }
}
