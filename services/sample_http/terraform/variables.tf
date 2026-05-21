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

variable "stickiness_enabled" {
  description = "Enable stickiness"
  default     = false
  type        = bool
}

variable "stickiness_maxage" {
  description = "Sticky cookie max age in seconds"
  default     = 30
  type        = number
}

variable "ingress_dns" {
  description = "Hostname to be used in ingress"
  type        = string
  default     = "testservice.test"
}
