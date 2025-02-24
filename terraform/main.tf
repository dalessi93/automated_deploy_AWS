resource "aws_instance" "traefik" {
  ami           = "ami-06e02ae7bdac6b938"
  instance_type = "t3.micro"
  subnet_id     = "subnet-0717aac9526c9ff4b"
  vpc_security_group_ids = [
    "sg-063f4ee98662f19a1"
  ]
  key_name               = "provisioner_DA"

  tags = {
    Name = "daniel_Traefik_instance"
  }
}