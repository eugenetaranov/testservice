variable "cluster_name" {
  description = "EKS cluster name"
  default     = ""
  type        = string
}

variable "namespace" {
  description = "Namespace"
  default     = "test"
  type        = string
}

variable "replicas" {
  description = "Number of replicas"
  default     = 1
  type        = number
}
