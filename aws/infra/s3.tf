resource "aws_s3_bucket" "reports" {
  bucket = var.report_s3_bucket
  acl    = "private"

  tags = {
    Name    = "${var.tag_project_name}_reports"
    project = var.tag_project_name
  }
}
