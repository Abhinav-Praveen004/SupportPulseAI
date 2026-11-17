"""Synthetic Data Generator for SupportPulse AI.

Generates 20,000 realistic IT service desk tickets across 12 months with:
- 10 IT categories, realistic text with templates, paraphrases, typos
- Latent frustration variable driving linguistic and behavioral cues
- Breach probability driven by priority, queue load, hour, and complexity
- Emerging VPN outage burst in the final 2 weeks for theme discovery
- Time-ordered splits (70% train, 15% val, 15% test)
- Writes data/tickets.csv and reports/data_profile.json
"""

import argparse
import csv
import json
import os
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple
import numpy as np

# Set deterministic random seeds
SEED = 42
random.seed(SEED)
np.random.seed(SEED)

CATEGORIES = [
    "Password/Access",
    "Network/VPN",
    "Email",
    "Hardware",
    "Software Install",
    "Application Error",
    "Security Incident",
    "Printer",
    "Cloud/Infrastructure",
    "Service Request",
]

CATEGORY_WEIGHTS = [0.18, 0.13, 0.11, 0.10, 0.14, 0.12, 0.03, 0.05, 0.05, 0.09]

TEAMS_FOR_CATEGORY = {
    "Password/Access": "IT Helpdesk",
    "Network/VPN": "Network Ops",
    "Email": "IT Helpdesk",
    "Hardware": "Endpoint Services",
    "Software Install": "Endpoint Services",
    "Application Error": "Application Support",
    "Security Incident": "Security Ops",
    "Printer": "IT Helpdesk",
    "Cloud/Infrastructure": "Cloud Infrastructure",
    "Service Request": "IT Helpdesk",
}

ALL_TEAMS = [
    "IT Helpdesk",
    "Network Ops",
    "Endpoint Services",
    "Application Support",
    "Cloud Infrastructure",
    "Security Ops",
]

PRIORITIES = ["P1", "P2", "P3", "P4"]
PRIORITY_WEIGHTS = [0.05, 0.18, 0.55, 0.22]
SLA_HOURS = {"P1": 4.0, "P2": 8.0, "P3": 24.0, "P4": 72.0}

DEPARTMENTS = [
    "Engineering",
    "Sales",
    "Finance",
    "Human Resources",
    "Marketing",
    "Operations",
    "Customer Support",
    "Legal",
]
DEPT_WEIGHTS = [0.25, 0.20, 0.15, 0.10, 0.10, 0.10, 0.06, 0.04]

CHANNELS = ["portal", "email", "slack", "phone"]
CHANNEL_WEIGHTS = [0.45, 0.35, 0.15, 0.05]

# Category Templates and Realism Vocabularies
TEMPLATES: Dict[str, Dict[str, List[str]]] = {
    "Password/Access": {
        "subjects": [
            "Password reset required for {system}",
            "Locked out of my {system} account",
            "Cannot access {system} after password expiration",
            "Urgent: MFA token reset for {system}",
            "Account unlock request: {system}",
            "Need permissions to access {folder}",
            "Single Sign-On (SSO) login loop in {system}",
            "Temporary access credentials needed for audit",
        ],
        "bodies": [
            "I tried logging into {system} this morning but it says my credentials have expired. Please reset my temporary password.",
            "My account has been locked after 3 unsuccessful attempts on {system}. I need this unlocked urgently to finish client reporting.",
            "I got a new phone and my authenticator app for {system} is no longer generating valid tokens. Can you reset my MFA?",
            "Unable to access {folder}. Getting permission denied error when attempting to open project documentation.",
            "Every time I try to log in via Okta to {system}, it redirects back to the login prompt. Please help resolve this.",
        ],
        "systems": ["Active Directory", "Okta", "Salesforce", "Jira", "Workday", "SAP", "GitHub", "AWS Console"],
        "folders": ["Finance Share", "HR Confidential", "Client Deliverables", "Engineering Specs", "Q4 Budget Drive"],
    },
    "Network/VPN": {
        "subjects": [
            "VPN connection keeps dropping every few minutes",
            "Cannot connect to corporate VPN from home",
            "AnyConnect gateway timeout error {code}",
            "GlobalProtect failed to establish secure tunnel",
            "Wi-Fi connection unstable on {floor} floor",
            "No internet connectivity in meeting room {room}",
            "Slow network speeds accessing internal file shares",
            "Split-tunnel routing issue with internal subnets",
        ],
        "bodies": [
            "My VPN disconnects every 5 to 10 minutes while working remotely. Gateway error code {code}. I have tried restarting my router.",
            "Cannot establish connection to the primary corporate VPN concentrator. Getting 'Remote gateway not responding'.",
            "Wi-Fi signal drops constantly on the {floor} floor near room {room}. Video calls keep freezing.",
            "I am unable to reach internal database servers over VPN while other websites work fine. Looks like DNS or route table issue.",
            "GlobalProtect client shows 'Connecting' indefinitely and then fails with SSL handshake timeout.",
        ],
        "codes": ["GW-504", "ERR-TIMEOUT-41", "TUN-FAIL-02", "SEC-701"],
        "floors": ["2nd", "3rd", "4th", "5th"],
        "rooms": ["Atlas", "Horizon", "Orion", "Apex", "Boardroom"],
    },
    "Email": {
        "subjects": [
            "Outlook crashing repeatedly on startup",
            "Mailbox storage limit exceeded notification",
            "Not receiving external emails from clients",
            "Need shared mailbox delegation for {team_name}",
            "Spam filter falsely quarantining important vendor emails",
            "Distribution list {dist_list} update request",
            "Calendar invites disappearing or showing wrong timezone",
            "Cannot send attachments larger than 10MB in Outlook",
        ],
        "bodies": [
            "My Outlook client crashes immediately upon launch with an unexpected error. I can only use webmail currently.",
            "I received an alert that my Exchange mailbox is at 99% capacity and cannot send any new messages. Please increase quota.",
            "We are not receiving emails from domain @partner-corp.com. It seems our spam gateway is blocking their mail servers.",
            "Please grant full access and 'Send As' permissions for the shared mailbox {team_name}@company.com to my user profile.",
            "Meeting calendar invitations sent from external clients are not showing up on my schedule or appear in UTC.",
        ],
        "team_names": ["billing-ops", "marketing-leads", "legal-contracts", "recruiting-team", "apac-support"],
        "dist_list": ["all-engineers", "apac-sales", "us-managers", "product-designers"],
    },
    "Hardware": {
        "subjects": [
            "Laptop screen flickering and going black intermittently",
            "USB-C dock not detecting external monitors",
            "MacBook battery swelling and trackpad unresponsive",
            "Lenovo ThinkPad keyboard keys {keys} not working",
            "Laptop overheating and fan running at full speed",
            "Headset microphone not detected in Teams or Zoom",
            "Damaged power adapter / charger replacement request",
            "Blue Screen of Death (BSOD) on boot: {bsod}",
        ],
        "bodies": [
            "My laptop display flashes repeatedly and turns black whenever the hinge is adjusted. Might be a loose display cable.",
            "The Dell Thunderbolt dock at my desk stopped outputting video to both external displays. USB peripherals still work.",
            "The lower chassis of my company MacBook appears swollen and the trackpad will no longer click. Potential battery hazard.",
            "My ThinkPad keyboard is malfunctioning. The {keys} keys do not register keystrokes. External USB keyboard works fine.",
            "Machine crashed with BSOD '{bsod}' twice today while running standard applications. Minidump attached if needed.",
        ],
        "keys": ["Spacebar and Enter", "T, Y, and U", "Shift and Ctrl", "Number row 1-5"],
        "bsod": ["CRITICAL_PROCESS_DIED", "DPC_WATCHDOG_VIOLATION", "KERNEL_DATA_INPAGE_ERROR", "SYSTEM_SERVICE_EXCEPTION"],
    },
    "Software Install": {
        "subjects": [
            "Software installation request: {software}",
            "License activation required for {software}",
            "Upgrade request for {software} to version {ver}",
            "Need admin privileges to install {software} for project",
            "Docker Desktop license key assignment for engineering",
            "IntelliJ IDEA Ultimate license renewal",
            "Requesting Figma Professional editor seat",
            "Install Python 3.11 and Node.js SDK on developer workstation",
        ],
        "bodies": [
            "Please install {software} on my workstation. I require it for upcoming development tasks in sprint 24.",
            "My license for {software} has expired and displays an unauthorized watermark. Please assign an active seat.",
            "I need administrative approval and push installation for {software} version {ver} to resolve a security patch.",
            "Requesting standard developer tooling pack including Docker Desktop, VS Code, and Postman on my newly issued machine.",
            "Can you provision an enterprise license seat for {software}? Approved by department manager.",
        ],
        "software": ["Docker Desktop", "IntelliJ IDEA", "Figma", "Postman Enterprise", "Adobe Acrobat Pro", "Tableau Desktop", "PyCharm Pro", "TablePlus"],
        "ver": ["2026.2", "4.15", "12.0.1", "3.8.4"],
    },
    "Application Error": {
        "subjects": [
            "Internal Server Error 500 when loading {app_name}",
            "Database connection timeout on {app_name} reporting module",
            "{app_name} freezing during bulk CSV export",
            "NullPointerException thrown when submitting form in {app_name}",
            "API endpoint returning 502 Bad Gateway for {app_name}",
            "Data synchronization mismatch between {app_name} and ERP",
            "Session timeout occurs immediately after logging into {app_name}",
            "Critical job failure in nightly {app_name} batch pipeline",
        ],
        "bodies": [
            "Users across sales are receiving 'HTTP 500 Internal Error' when trying to access the {app_name} dashboard.",
            "When running the monthly data export in {app_name}, the request hangs for 3 minutes and times out with error 504.",
            "Encountering an unhandled exception in {app_name} with stack trace showing failed connection to primary DB replica.",
            "The customer sync pipeline in {app_name} failed at step 4. Customer records created today are not reflecting in Salesforce.",
            "Application freezes completely whenever clicking 'Generate Invoice' in {app_name}. Requires killing process in Task Manager.",
        ],
        "app_name": ["CustomerPortal", "BillingService", "InventoryManager", "AnalyticsHub", "PayrollApp", "CRM Gateway"],
    },
    "Security Incident": {
        "subjects": [
            "Suspicious phishing email targeting {dept} employees",
            "Endpoint antivirus alert: potential malware detected on host {host}",
            "Unauthorized Duo MFA push notification received at {time}",
            "Potential data exposure: public S3 bucket link detected",
            "Ransomware warning pop-up appeared in browser",
            "Lost or stolen company laptop reported by employee",
            "Suspicious foreign IP login detected on {system}",
            "Security compliance audit flag on unencrypted external drive",
        ],
        "bodies": [
            "Multiple team members in {dept} received a fraudulent email purporting to be from CEO requesting urgent wire transfer. Headers attached.",
            "CrowdStrike Falcon flagged a suspicious executable running from AppData on host {host}. Device has been disconnected from network.",
            "I received two unexpected Duo 2FA push notifications at {time} while sleeping. I did not initiate these logins. Suspect credential compromise.",
            "An employee accidentally shared a Google Drive folder containing customer PII to 'Anyone with the link'. Link has been disabled, review needed.",
            "Company issued MacBook was stolen from vehicle overnight. Please trigger remote wipe immediately via Jamf.",
        ],
        "host": ["LAPTOP-ENG-84", "WS-FIN-12", "DEV-NODE-99", "DESK-MKT-03"],
        "time": ["02:14 AM", "03:45 AM", "11:30 PM", "04:10 AM"],
    },
    "Printer": {
        "subjects": [
            "Network printer {printer} offline and not responding",
            "Paper jam error code on {floor} floor copier",
            "Toner cartridge empty on printer {printer}",
            "Print jobs stuck in print spooler queue on Windows",
            "Printer producing streaked and illegible barcode pages",
            "Badge scan release not working on multi-function printer",
            "Driver installation failing for secure badge printing",
            "Color prints coming out monochrome on {printer}",
        ],
        "bodies": [
            "The HP LaserJet printer on {floor} floor ({printer}) is showing offline in Windows settings. Power cycle did not resolve.",
            "There is a persistent paper jam in tray 2 of the main office copier. The clear jam lever does not release the jammed sheet.",
            "Printer {printer} has been completely out of black toner since yesterday. Urgent contracts need to be printed.",
            "Multiple documents are stuck in the print queue with status 'Error - Printing'. Cannot delete or cancel jobs without admin rights.",
            "Badge tap at the Xerox multi-function printer fails to authenticate. Screen says 'Card reader communication error'.",
        ],
        "printer": ["PRN-FL2-NORTH", "PRN-FL3-COLOR", "PRN-EXEC-SUITE", "PRN-HR-SECURE", "PRN-ENG-CORRIDOR"],
        "floors": ["1st", "2nd", "3rd", "4th"],
    },
    "Cloud/Infrastructure": {
        "subjects": [
            "Production Kubernetes cluster pod CrashLoopBackOff in {env}",
            "AWS IAM permission denied when assuming role {role}",
            "Terraform state lock error preventing deployment to {env}",
            "EC2 instance {instance} unresponsive / health check failed",
            "High CPU and memory utilization alert on database cluster {cluster}",
            "SSL certificate expiry warning for domain {domain}",
            "Ingress controller returning 503 Service Unavailable in {env}",
            "S3 bucket replication lag exceeding 4 hours",
        ],
        "bodies": [
            "The backend deployment pods in Kubernetes cluster ({env}) are failing liveness probes and restarting repeatedly.",
            "CI/CD pipeline failed during terraform apply because the DynamoDB lock for state file is held by an abandoned runner.",
            "AWS CloudWatch alert: Database cluster {cluster} has maintained 98% CPU utilization for over 30 minutes. Risk of failover.",
            "Production instance {instance} failed system status check 2/2. Unable to SSH or connect via SSM session manager.",
            "SSL certificate for {domain} expires in 48 hours. Let's Encrypt automated cert-manager renewal appears to be failing DNS validation.",
        ],
        "env": ["prod-us-east-1", "staging-eu-west-1", "dev-k8s-cluster", "prod-apac-southeast-1"],
        "role": ["arn:aws:iam::1234:role/DataPipelineDeployer", "arn:aws:iam::1234:role/K8sNodeOperator"],
        "instance": ["i-0a8b9c1d2e3f4", "i-077f98ab12cde", "i-0912bcde45f6a"],
        "cluster": ["rds-postgres-prod-main", "aurora-mysql-analytics", "redis-session-cache"],
        "domain": ["api.company.com", "app.customerportal.net", "sso.internal.corp"],
    },
    "Service Request": {
        "subjects": [
            "Request for secondary 27-inch 4K monitor for home office",
            "Temporary guest Wi-Fi credentials for external auditors",
            "Hardware requisition for new engineering hire starting Monday",
            "Ergonomic chair and standing desk converter request",
            "Headset replacement: Jabra wireless noise-cancelling",
            "YubiKey hardware security key requisition",
            "Conference room AV equipment setup for town hall meeting",
            "Loaner laptop request for international business travel",
        ],
        "bodies": [
            "Per the remote work policy, I would like to request an external 27-inch monitor for my home office setup. Manager has approved.",
            "We have 4 external financial auditors visiting next week from Monday to Thursday. Please generate guest Wi-Fi access tokens.",
            "New Senior Software Engineer starting on Monday in {dept}. Need standard laptop, monitor, YubiKey, and desk setup prepared.",
            "My current headset has a broken headband. Requesting a replacement noise-cancelling headset for client calls.",
            "Traveling to Europe for customer summits next month. Requesting an encrypted loaner laptop per travel security guidelines.",
        ],
        "dept": ["Engineering", "Finance", "Sales", "Customer Support"],
    },
}

# Incident burst templates (VPN outage cluster in final 2 weeks)
VPN_BURST_SUBJECTS = [
    "URGENT: Corporate VPN completely down - cannot connect",
    "GlobalProtect VPN gateway timeout across entire company",
    "VPN server returning error: Gateway Authentication Failed",
    "All remote employees disconnected from VPN simultaneously",
    "VPN handshake failure on US-East concentrator",
    "Cannot reach internal services: VPN tunnel terminated",
    "P1: VPN outage affecting all engineering and sales staff",
    "Remote access down: GlobalProtect connection error 504",
]

VPN_BURST_BODIES = [
    "Corporate VPN disconnected suddenly and cannot reconnect. GlobalProtect reports 'Server certificate untrusted' and gateway timeout.",
    "The entire remote workforce cannot access internal servers. VPN client fails at 98% with gateway connection error.",
    "Emergency: VPN gateway appears to be crashing or overloaded. No one on our remote team can connect to production or databases.",
    "VPN went down 10 minutes ago. Getting 'Gateway is not responding'. Multiple team members experiencing the exact same issue.",
    "Cannot establish VPN tunnel to US-East or US-West gateways. Halting client delivery work until resolved.",
]

FRUSTRATION_CUES = [
    "THIS IS TOTALLY UNACCEPTABLE!",
    "STILL NOT WORKING AFTER MULTIPLE ATTEMPTS!",
    "PLEASE ESCALATE THIS TO A SENIOR ENGINEER IMMEDIATELY!",
    "This is the third time I am submitting this ticket!",
    "BLOCKING OUR ENTIRE SPRINT AND CLIENT DEADLINES!",
    "Why does this keep happening every single week???",
    "No one has responded to my previous request!",
    "URGENT: We are losing revenue right now due to this issue!",
]

TYPO_DICT = {
    "password": "passwrod",
    "connection": "conection",
    "the": "teh",
    "cannot": "cant",
    "error": "eror",
    "please": "plz",
    "urgent": "urgnet",
    "access": "acces",
    "working": "wrking",
    "help": "hlp",
}


def inject_typos(text: str, typo_prob: float = 0.20) -> str:
    """Inject realistic human typing errors."""
    words = text.split()
    new_words = []
    for word in words:
        clean_word = word.lower().strip(".,!?:;")
        if clean_word in TYPO_DICT and random.random() < typo_prob:
            rep = TYPO_DICT[clean_word]
            if word.isupper():
                rep = rep.upper()
            elif word.istitle():
                rep = rep.title()
            new_words.append(rep)
        else:
            new_words.append(word)
    return " ".join(new_words)


def fill_template(template_str: str, meta: Dict[str, Any]) -> str:
    """Safely format template with random metadata."""
    res = template_str
    for key, values in meta.items():
        placeholder = "{" + key + "}"
        if placeholder in res:
            res = res.replace(placeholder, str(random.choice(values)))
    # Default fallback for unformatted placeholders
    for generic in ["system", "folder", "code", "floor", "room", "team_name", "dist_list", "keys", "bsod", "software", "ver", "app_name", "host", "time", "printer", "env", "role", "instance", "cluster", "domain", "dept"]:
        placeholder = "{" + generic + "}"
        if placeholder in res:
            res = res.replace(placeholder, "CoreSystem")
    return res


def generate_ticket_text(category: str, frustration_level: float, is_vpn_burst: bool = False) -> Tuple[str, str]:
    """Generate realistic subject and multi-sentence body with frustration cues and typos."""
    if is_vpn_burst:
        subject = random.choice(VPN_BURST_SUBJECTS)
        body = random.choice(VPN_BURST_BODIES)
    else:
        tmpl_cat = TEMPLATES.get(category, TEMPLATES["Service Request"])
        meta = {k: v for k, v in tmpl_cat.items() if k not in ("subjects", "bodies")}
        subject = fill_template(random.choice(tmpl_cat["subjects"]), meta)
        body_sentences = [fill_template(random.choice(tmpl_cat["bodies"]), meta)]

        # Add 1 to 3 additional sentences for body realism
        sentence_pool = [
            "I have already tried restarting my computer and clearing browser cache.",
            "This started happening right after the system update yesterday.",
            "Please let me know if you need any additional diagnostic logs or screenshots.",
            "I will be available via Slack if you need me to reproduce the error.",
            "This is impacting my team's ability to complete daily client deliverables.",
            "Please confirm once this has been addressed.",
        ]
        num_extra = random.randint(1, 3)
        body_sentences.extend(random.sample(sentence_pool, num_extra))
        body = " ".join(body_sentences)

    # Frustration impact: high frustration adds angry cues, ALL CAPS sentences, exclamation marks
    if frustration_level > 0.65:
        cue = random.choice(FRUSTRATION_CUES)
        if random.random() < 0.6:
            body = f"{cue} {body}"
        else:
            body = f"{body} {cue}"
        if frustration_level > 0.85:
            subject = subject.upper()

    # Inject typos with probability proportional to haste/frustration
    typo_rate = 0.10 + (frustration_level * 0.20)
    subject = inject_typos(subject, typo_prob=typo_rate)
    body = inject_typos(body, typo_prob=typo_rate)

    return subject, body


def generate_synthetic_dataset(
    count: int = 20000,
    output_path: str = "data/tickets.csv",
    report_path: str = "reports/data_profile.json",
    start_date: datetime | None = None,
    seed: int = SEED,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Generate reproducible 20,000 tickets dataset and data profiling report."""
    random.seed(seed)
    np.random.seed(seed)
    if start_date is None:
        # Fixed reference point for perfect reproducibility
        now = datetime(2026, 11, 17, 12, 0, 0, tzinfo=timezone.utc)
        start_date = now - timedelta(days=365)
    else:
        now = start_date + timedelta(days=365)

    tickets: List[Dict[str, Any]] = []

    # Category distribution weights
    cat_weights = np.array(CATEGORY_WEIGHTS)
    cat_weights = cat_weights / cat_weights.sum()

    # Time distribution: uniform over 365 days, with burst in final 14 days
    seconds_in_year = 365 * 86400
    vpn_burst_start = now - timedelta(days=14)
    # Burst is min(550, ~3% of total tickets)
    vpn_burst_ticket_count = min(550, max(5, int(count * 0.03))) if count >= 50 else 0

    base_count = count - vpn_burst_ticket_count

    # Pre-generate timestamps chronologically
    random_offsets = np.sort(np.random.uniform(0, seconds_in_year, base_count))
    created_datetimes = [start_date + timedelta(seconds=float(off)) for off in random_offsets]

    # Pre-generate VPN burst timestamps in last 14 days
    burst_offsets = np.sort(np.random.uniform(0, 14 * 86400, vpn_burst_ticket_count))
    burst_datetimes = [vpn_burst_start + timedelta(seconds=float(off)) for off in burst_offsets]

    # Merge and sort all datetimes
    all_events: List[Tuple[datetime, bool]] = [(dt, False) for dt in created_datetimes] + [
        (dt, True) for dt in burst_datetimes
    ]
    all_events.sort(key=lambda x: x[0])

    # Track simulated queue load per team
    open_tickets_per_team: Dict[str, int] = {team: 0 for team in ALL_TEAMS}

    # Agents pool
    agents_pool = [f"AGT-{idx:03d}" for idx in range(101, 141)]  # 40 agents

    for idx, (created_at, is_burst) in enumerate(all_events, start=1):
        ticket_id = f"TCK-{idx:05d}"
        requester_id = f"USR-{random.randint(1001, 2500):04d}"
        department = np.random.choice(DEPARTMENTS, p=DEPT_WEIGHTS)
        channel = np.random.choice(CHANNELS, p=CHANNEL_WEIGHTS)

        if is_burst:
            category = "Network/VPN"
            # High priority during outage
            priority = np.random.choice(["P1", "P2", "P3"], p=[0.30, 0.50, 0.20])
            assigned_team = "Network Ops"
        else:
            category = np.random.choice(CATEGORIES, p=cat_weights)
            priority = np.random.choice(PRIORITIES, p=PRIORITY_WEIGHTS)
            assigned_team = TEAMS_FOR_CATEGORY[category]

        # 8-10% ambiguity / noise in category label (Section 6 requirement)
        is_ambiguous = random.random() < 0.09
        if is_ambiguous and not is_burst:
            # Shift category label slightly to simulate human labeling noise
            noisy_category = random.choice([c for c in CATEGORIES if c != category])
        else:
            noisy_category = category

        # Latent requester frustration variable (Beta distribution)
        frustration = float(np.random.beta(1.5, 4.0))
        if is_burst:
            frustration = min(1.0, frustration + 0.35)

        # Frustration influences contact_count, reopen_count, escalated
        if frustration > 0.75:
            contact_count = random.randint(3, 7)
            reopen_count = random.randint(1, 3)
            escalated = random.random() < 0.85
        elif frustration > 0.45:
            contact_count = random.randint(2, 4)
            reopen_count = random.randint(0, 1)
            escalated = random.random() < 0.35
        else:
            contact_count = random.randint(1, 2)
            reopen_count = 0
            escalated = False

        subject, body = generate_ticket_text(noisy_category, frustration, is_vpn_burst=is_burst)

        sla_hours = SLA_HOURS[priority]

        # Calculate SLA breach probability driven by:
        # - Priority (P1 4h tighter -> higher vulnerability to off-hours)
        # - Hour of day (nights 18:00 - 08:00 have fewer agents)
        # - Weekend (Saturdays/Sundays)
        # - Team load
        # - Category complexity
        hour = created_at.hour
        is_night = hour < 8 or hour >= 18
        is_weekend = created_at.weekday() >= 5
        team_load = open_tickets_per_team.get(assigned_team, 10)

        complexity_factor = {
            "Security Incident": 1.4,
            "Cloud/Infrastructure": 1.3,
            "Application Error": 1.25,
            "Hardware": 1.15,
            "Network/VPN": 1.10,
            "Email": 0.95,
            "Software Install": 0.90,
            "Printer": 0.85,
            "Password/Access": 0.70,
            "Service Request": 0.80,
        }.get(noisy_category, 1.0)

        # Baseline breach risk score
        breach_logits = (
            -1.4
            + (0.6 if priority == "P1" else 0.3 if priority == "P2" else -0.1 if priority == "P3" else -0.5)
            + (0.7 if is_night else 0.0)
            + (0.8 if is_weekend else 0.0)
            + (0.02 * min(team_load, 50))
            + (0.5 * (complexity_factor - 1.0))
            + (0.4 * frustration)
            + np.random.normal(0, 0.35)
        )
        breach_prob = float(1.0 / (1.0 + np.exp(-breach_logits)))
        will_breach = breach_prob > 0.50

        # Simulate resolution duration
        if will_breach:
            actual_duration_hours = sla_hours * float(np.random.uniform(1.05, 3.2))
        else:
            actual_duration_hours = sla_hours * float(np.random.uniform(0.15, 0.95))

        # First response time (15 mins to 2 hours)
        first_resp_minutes = random.uniform(10, min(180, actual_duration_hours * 60 * 0.4))
        first_response_at = created_at + timedelta(minutes=first_resp_minutes)

        # Status: tickets created recently (in last 5 days) might still be open
        days_from_end = (now - created_at).total_seconds() / 86400.0
        if days_from_end <= 3:
            # 60% open for very recent
            is_open = random.random() < 0.60
        elif days_from_end <= 7:
            # 25% open
            is_open = random.random() < 0.25
        elif days_from_end <= 14:
            # 10% open
            is_open = random.random() < 0.10
        else:
            # 1% historical open backlog
            is_open = random.random() < 0.01

        if is_open:
            status = random.choice(["open", "in_progress", "waiting_on_customer"])
            resolved_at = None
            # Check if currently breached based on elapsed time to 'now'
            elapsed_hours = (now - created_at).total_seconds() / 3600.0
            breached = elapsed_hours > sla_hours
            open_tickets_per_team[assigned_team] = open_tickets_per_team.get(assigned_team, 0) + 1
            agent_id = random.choice(agents_pool) if status != "open" else None
        else:
            status = random.choice(["resolved", "closed"])
            resolved_at = created_at + timedelta(hours=actual_duration_hours)
            breached = will_breach
            agent_id = random.choice(agents_pool)

        ticket_record = {
            "ticket_id": ticket_id,
            "created_at": created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "subject": subject,
            "body": body,
            "requester_id": requester_id,
            "department": department,
            "channel": channel,
            "category": noisy_category,
            "true_category": category,  # Kept for evaluation sanity checking
            "priority": priority,
            "assigned_team": assigned_team,
            "agent_id": agent_id,
            "first_response_at": first_response_at.strftime("%Y-%m-%d %H:%M:%S"),
            "resolved_at": resolved_at.strftime("%Y-%m-%d %H:%M:%S") if resolved_at else "",
            "sla_hours": sla_hours,
            "breached": breached,
            "reopen_count": reopen_count,
            "contact_count": contact_count,
            "escalated": escalated,
            "status": status,
            "frustration_score_latent": round(frustration * 100, 2),
            "is_vpn_burst": is_burst,
        }
        tickets.append(ticket_record)

    # Save to CSV
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = list(tickets[0].keys())
    with open(output_file, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(tickets)

    # Compute data profile report
    total_count = len(tickets)
    cat_counts = {}
    prio_counts = {}
    team_counts = {}
    dept_counts = {}
    channel_counts = {}
    status_counts = {}
    breached_count = 0
    escalated_count = 0

    for t in tickets:
        cat_counts[t["category"]] = cat_counts.get(t["category"], 0) + 1
        prio_counts[t["priority"]] = prio_counts.get(t["priority"], 0) + 1
        team_counts[t["assigned_team"]] = team_counts.get(t["assigned_team"], 0) + 1
        dept_counts[t["department"]] = dept_counts.get(t["department"], 0) + 1
        channel_counts[t["channel"]] = channel_counts.get(t["channel"], 0) + 1
        status_counts[t["status"]] = status_counts.get(t["status"], 0) + 1
        if t["breached"]:
            breached_count += 1
        if t["escalated"]:
            escalated_count += 1

    # Time-ordered split indices
    train_size = int(total_count * 0.70)
    val_size = int(total_count * 0.15)
    test_size = total_count - train_size - val_size

    profile = {
        "metadata": {
            "dataset_name": "SupportPulse AI Synthetic IT Tickets",
            "is_synthetic": True,
            "generator_seed": SEED,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_tickets": total_count,
            "time_range": {
                "start": tickets[0]["created_at"],
                "end": tickets[-1]["created_at"],
                "span_days": 365,
            },
        },
        "splits": {
            "train": {"count": train_size, "pct": 70.0, "start": tickets[0]["created_at"], "end": tickets[train_size - 1]["created_at"]},
            "validation": {"count": val_size, "pct": 15.0, "start": tickets[train_size]["created_at"], "end": tickets[train_size + val_size - 1]["created_at"]},
            "test": {"count": test_size, "pct": 15.0, "start": tickets[train_size + val_size]["created_at"], "end": tickets[-1]["created_at"]},
        },
        "distributions": {
            "categories": cat_counts,
            "priorities": prio_counts,
            "teams": team_counts,
            "departments": dept_counts,
            "channels": channel_counts,
            "statuses": status_counts,
        },
        "key_metrics": {
            "breach_rate_pct": round((breached_count / total_count) * 100, 2),
            "escalation_rate_pct": round((escalated_count / total_count) * 100, 2),
            "vpn_burst_tickets": vpn_burst_ticket_count,
            "open_tickets_count": sum(status_counts.get(s, 0) for s in ["open", "in_progress", "waiting_on_customer"]),
        },
    }

    report_file = Path(report_path)
    report_file.parent.mkdir(parents=True, exist_ok=True)
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2)

    return tickets, profile


def populate_database(csv_path: str = "data/tickets.csv"):
    """Populate database from generated CSV file."""
    from backend.app.db.session import SessionLocal, engine, Base
    from backend.app.db.models import Ticket, User
    from backend.app.services.importer import import_tickets_from_csv
    import bcrypt

    # Ensure tables exist
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # 1. Seed demo users
        demo_users = [
            ("admin", "admin@supportpulse.local", "admin123", "admin", "System Administrator"),
            ("manager", "manager@supportpulse.local", "manager123", "manager", "IT Desk Manager"),
            ("agent", "agent@supportpulse.local", "agent123", "agent", "Sarah Jenkins (Tier 1 Agent)"),
        ]
        for username, email, pwd, role, full_name in demo_users:
            if not db.query(User).filter(User.username == username).first():
                salt = bcrypt.gensalt()
                hashed = bcrypt.hashpw(pwd.encode("utf-8"), salt).decode("utf-8")
                db.add(User(
                    username=username,
                    email=email,
                    hashed_password=hashed,
                    role=role,
                    full_name=full_name,
                    is_active=True,
                ))
        db.commit()

        # 2. Seed tickets
        with open(csv_path, "r", encoding="utf-8") as f:
            content = f.read()
            imported, errors, err_list = import_tickets_from_csv(db, content)
            print(f"Database populated: {imported} tickets imported ({errors} skipped/errors).")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate synthetic ticket dataset for SupportPulse AI")
    parser.add_argument("--count", type=int, default=20000, help="Number of tickets to generate")
    parser.add_argument("--output", type=str, default="data/tickets.csv", help="Output CSV path")
    parser.add_argument("--report", type=str, default="reports/data_profile.json", help="Data profile JSON report path")
    parser.add_argument("--populate-db", action="store_true", help="Populate SQLite database after generating")
    args = parser.parse_args()

    print(f"Generating {args.count} synthetic tickets with random seed {SEED}...")
    tickets, profile = generate_synthetic_dataset(count=args.count, output_path=args.output, report_path=args.report)
    print(f"Successfully generated {len(tickets)} tickets to {args.output}")
    print(f"Data profile report written to {args.report}")
    print(f"Breach Rate: {profile['key_metrics']['breach_rate_pct']}% | Escalated: {profile['key_metrics']['escalation_rate_pct']}%")

    if args.populate_db:
        print("Populating local database...")
        populate_database(args.output)
