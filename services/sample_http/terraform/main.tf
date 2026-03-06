data "aws_eks_cluster" "cluster" {
  name = var.cluster_name
}

data "aws_eks_cluster_auth" "cluster" {
  name = data.aws_eks_cluster.cluster.id
}

provider "kubernetes" {
  host                   = data.aws_eks_cluster.cluster.endpoint
  cluster_ca_certificate = base64decode(data.aws_eks_cluster.cluster.certificate_authority[0].data)
  token                  = data.aws_eks_cluster_auth.cluster.token
}

resource "kubernetes_namespace_v1" "default" {
  metadata {
    name = var.namespace
  }
}

resource "kubernetes_deployment" "testservice" {
  metadata {
    name      = "testservice"
    namespace = kubernetes_namespace_v1.default.metadata[0].name
  }

  spec {
    replicas = var.replicas

    selector {
      match_labels = {
        app = "testservice"
      }
    }

    template {
      metadata {
        labels = {
          app = "testservice"
        }
      }

      spec {
        termination_grace_period_seconds = 120

        container {
          name  = "testservice"
          image = "eugenetaranov/testservice:latest"

          image_pull_policy = "Always"

          port {
            container_port = 8080
          }

          liveness_probe {
            http_get {
              path   = "/health"
              port   = 8080
              scheme = "HTTP"
            }

            initial_delay_seconds = 10
            timeout_seconds       = 1
            period_seconds        = 5
            success_threshold     = 1
            failure_threshold     = 2
          }

          readiness_probe {
            http_get {
              path   = "/health"
              port   = 8080
              scheme = "HTTP"
            }

            initial_delay_seconds = 10
            timeout_seconds       = 1
            period_seconds        = 5
            success_threshold     = 1
            failure_threshold     = 2
          }

          startup_probe {
            http_get {
              path   = "/health"
              port   = 8080
              scheme = "HTTP"
            }

            timeout_seconds   = 1
            period_seconds    = 2
            success_threshold = 1
            failure_threshold = 2
          }

          lifecycle {
            pre_stop {
              exec {
                command = ["/bin/sh", "/app/hooks/pre_stop.sh"]
              }
            }
          }

          env {
            name  = "NAME"
            value = "testservice"
          }
        }
      }
    }
  }
}

resource "kubernetes_service_v1" "testservice" {
  metadata {
    name      = "testservice"
    namespace = kubernetes_namespace_v1.default.metadata[0].name

    annotations = {
      "traefik.ingress.kubernetes.io/service.sticky.cookie"        = var.stickiness_enabled ? "true" : "false"
      "traefik.ingress.kubernetes.io/service.sticky.cookie.name"   = var.stickiness_enabled ? "testservice" : ""
      "traefik.ingress.kubernetes.io/service.sticky.cookie.maxage" = var.stickiness_enabled ? "30" : ""
    }
  }

  spec {
    port {
      port        = 8080
      target_port = 8080
      protocol    = "TCP"
      name        = "http"
    }

    selector = {
      app = "testservice"
    }
  }
}

resource "kubernetes_ingress_v1" "testservice" {
  metadata {
    name      = "testservice"
    namespace = kubernetes_namespace_v1.default.metadata[0].name
    annotations = {
      "kubernetes.io/ingress.class" = "internal"
    }
  }

  spec {
    rule {
      host = "testservice.local"
      http {
        path {
          path = "/"
          backend {
            service {
              name = "testservice"
              port {
                name = "http"
              }
            }
          }
        }
      }
    }
  }
}
