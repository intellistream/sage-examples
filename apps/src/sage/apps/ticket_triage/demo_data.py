"""Demo data for the customer support ticket triage MVP."""

from __future__ import annotations

from .models import HistoricalResolution, KnowledgeBaseArticle, TicketEvent


def build_demo_tickets() -> list[TicketEvent]:
    return [
        TicketEvent(
            ticket_id="T-1001",
            channel="email",
            customer_id="CUST-001",
            subject="账号无法登录",
            message="我今天早上开始无法登录系统，提示账号锁定，请帮我处理。",
            created_at="2026-04-20T09:00:00",
            attachments=["login-error-screenshot.png"],
            customer_tier="standard",
        ),
        TicketEvent(
            ticket_id="T-1002",
            channel="form",
            customer_id="CUST-002",
            subject="申请退款",
            message="订单已经取消，但仍然扣费，请帮我退款。",
            created_at="2026-04-20T09:05:00",
            customer_tier="standard",
        ),
        TicketEvent(
            ticket_id="T-1003",
            channel="chat",
            customer_id="CUST-003",
            subject="订单还没到",
            message="物流显示卡住了，我想知道订单为什么延迟。",
            created_at="2026-04-20T09:08:00",
            customer_tier="enterprise",
        ),
        TicketEvent(
            ticket_id="T-1004",
            channel="email",
            customer_id="CUST-004",
            subject="电子发票怎么下载",
            message="请问电子发票入口在哪里，我需要下载报销。",
            created_at="2026-04-20T09:12:00",
            customer_tier="standard",
        ),
        TicketEvent(
            ticket_id="T-1005",
            channel="chat",
            customer_id="CUST-005",
            subject="系统报错 500",
            message="提交工单时页面报 500 错误，附件里有报错截图。",
            created_at="2026-04-20T09:16:00",
            attachments=["500-error-screenshot.png"],
            customer_tier="vip",
        ),
        TicketEvent(
            ticket_id="T-1006",
            channel="email",
            customer_id="CUST-006",
            subject="投诉升级",
            message="我已经等待两天了还没人处理，请立即升级给主管。",
            created_at="2026-04-20T09:21:00",
            customer_tier="vip",
        ),
        TicketEvent(
            ticket_id="T-1007",
            channel="chat",
            customer_id="CUST-001",
            subject="还是无法登录",
            message="刚才的账号锁定还没恢复，我现在还是无法登录，麻烦尽快处理。",
            created_at="2026-04-20T09:28:00",
            attachments=["second-login-error.png"],
            customer_tier="standard",
        ),
        TicketEvent(
            ticket_id="T-1008",
            channel="form",
            customer_id="CUST-007",
            subject="重复扣费",
            message="系统显示支付失败，但是银行卡被重复扣费两次。",
            created_at="2026-04-20T09:35:00",
            customer_tier="vip",
        ),
        TicketEvent(
            ticket_id="T-1009",
            channel="email",
            customer_id="CUST-008",
            subject="想问一下套餐功能",
            message="想了解专业版套餐包含哪些功能，是否支持导出。",
            created_at="2026-04-20T09:40:00",
            customer_tier="standard",
        ),
        TicketEvent(
            ticket_id="T-1010",
            channel="chat",
            customer_id="CUST-009",
            subject="物流更新太慢",
            message="订单一直没有新的物流信息，我需要今天确认能否送达。",
            created_at="2026-04-20T09:45:00",
            customer_tier="enterprise",
        ),
    ]


def build_demo_knowledge_articles() -> list[KnowledgeBaseArticle]:
    return [
        KnowledgeBaseArticle(
            article_id="KB-LOGIN-001",
            title="账号锁定处理指南",
            intent="login_issue",
            keywords=["无法登录", "账号锁定", "登录失败", "密码错误"],
            answer_template="您好，账号锁定通常可通过重置密码和二次验证解除，我们已为您附上自助恢复入口。",
            assigned_team="technical_support",
        ),
        KnowledgeBaseArticle(
            article_id="KB-REFUND-001",
            title="退款到账与重复扣费说明",
            intent="refund_request",
            keywords=["退款", "重复扣费", "取消订单", "支付失败"],
            answer_template="您好，退款工单已进入财务审核队列，重复扣费场景会优先核验交易流水并原路退回。",
            assigned_team="billing_ops",
        ),
        KnowledgeBaseArticle(
            article_id="KB-INVOICE-001",
            title="电子发票下载入口",
            intent="invoice_issue",
            keywords=["发票", "电子发票", "下载", "报销"],
            answer_template="您好，您可以在订单详情页的发票中心下载电子发票，如仍无法查看，请回复订单号。",
            assigned_team="billing_ops",
        ),
        KnowledgeBaseArticle(
            article_id="KB-ORDER-001",
            title="物流延迟查询与补偿政策",
            intent="order_delay",
            keywords=["物流", "延迟", "订单", "送达"],
            answer_template="您好，我们已收到您的物流延迟反馈，可先通过订单页查看最新轨迹，若超出承诺时效将补偿积分。",
            assigned_team="order_ops",
        ),
        KnowledgeBaseArticle(
            article_id="KB-GENERAL-001",
            title="套餐功能说明",
            intent="general_inquiry",
            keywords=["套餐", "功能", "导出", "专业版"],
            answer_template="您好，专业版支持导出、权限管理和自动报表，详细能力已为您附在回复中。",
            assigned_team="l1_support",
        ),
    ]


def build_demo_historical_resolutions() -> list[HistoricalResolution]:
    return [
        HistoricalResolution(
            case_id="CASE-LOGIN-007",
            title="企业用户账号锁定恢复",
            intent="login_issue",
            keywords=["账号锁定", "无法登录", "二次验证"],
            resolution_template="历史案例显示，此类问题通常由连续输错密码触发，建议先执行密码重置，再检查验证码设备状态。",
            assigned_team="technical_support",
        ),
        HistoricalResolution(
            case_id="CASE-REFUND-003",
            title="重复扣费人工退款处理",
            intent="refund_request",
            keywords=["重复扣费", "退款", "交易流水"],
            resolution_template="历史上该问题通常由支付网关重试引起，需要财务核对流水并在 1 个工作日内原路退回。",
            assigned_team="billing_ops",
        ),
        HistoricalResolution(
            case_id="CASE-ORDER-011",
            title="物流延迟升级协调",
            intent="order_delay",
            keywords=["物流", "延迟", "今天送达", "催办"],
            resolution_template="相似案例一般会同步物流承运商并由订单团队人工催办，高价值客户会附带补偿说明。",
            assigned_team="order_ops",
        ),
        HistoricalResolution(
            case_id="CASE-TECH-002",
            title="500 报错排查流程",
            intent="technical_support",
            keywords=["500", "报错", "截图", "提交失败"],
            resolution_template="同类问题通常需要先收集报错截图、请求时间和账号信息，再交由技术支持排查服务日志。",
            assigned_team="technical_support",
        ),
        HistoricalResolution(
            case_id="CASE-COMPLAINT-004",
            title="主管升级客诉处理",
            intent="complaint_escalation",
            keywords=["投诉", "升级", "立即处理", "等待两天"],
            resolution_template="类似客诉应直接升级给当班主管，并在 30 分钟内给出人工回访。",
            assigned_team="duty_manager",
        ),
    ]


def build_demo_summary() -> dict[str, int]:
    tickets = build_demo_tickets()
    return {
        "ticket_count": len(tickets),
        "channel_count": len({ticket.channel for ticket in tickets}),
        "customer_count": len({ticket.customer_id for ticket in tickets}),
        "knowledge_article_count": len(build_demo_knowledge_articles()),
        "historical_case_count": len(build_demo_historical_resolutions()),
    }
