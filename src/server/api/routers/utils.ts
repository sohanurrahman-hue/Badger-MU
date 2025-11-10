// 🧩 Helper: generate Manhattan University–themed HTML email body
interface BodyParams {
  recipientName: string;
  awardName: string;
  issuerName: string;
  credentialId: string;
  awardUrl: string;
  linkedInUrl?: string;
}

export const body = ({
  recipientName,
  awardName,
  issuerName,
  credentialId,
  awardUrl,
  linkedInUrl = "https://www.linkedin.com/profile/add",
}: BodyParams): string => `
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>${awardName} – Manhattan University</title>
  <style>
    body {margin:0;padding:0;font-family:"Segoe UI",Roboto,Arial,sans-serif;background:#f5f7f9;color:#1f2937;}
    .container{max-width:640px;margin:30px auto;background:#fff;border-radius:12px;
               box-shadow:0 4px 16px rgba(0,0,0,0.08);}
    .header{background:#006747;color:#fff;padding:20px 32px;display:flex;align-items:center;gap:12px;}
    .header h1{font-size:20px;font-weight:600;margin:0;}
    .content{padding:28px 32px;}
    .content h2{color:#006747;font-size:22px;margin-bottom:12px;}
    .btn{display:inline-block;background:#ffd200;color:#004b23;text-decoration:none;
         padding:10px 18px;font-weight:600;border-radius:8px;margin-top:10px;}
    .footer{font-size:12px;color:#6b7280;padding:16px 32px 24px;background:#f3f4f6;border-top:1px solid #e5e7eb;}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>Manhattan University</h1>
    </div>
    <div class="content">
      <h2>Congratulations, ${recipientName}!</h2>
      <p>
        You have been awarded the <strong>${awardName}</strong> by <strong>${issuerName}</strong>.
      </p>
      <p>
        Credential ID: <code>${credentialId}</code><br/>
        View your credential here:<br/>
        <a class="btn" href="${awardUrl}" target="_blank">View Certificate</a>
      </p>
      <p style="margin-top:20px">
        Add your achievement to your LinkedIn profile:
      </p>
      <p>
        <a class="btn" href="${linkedInUrl}" target="_blank">Add to LinkedIn</a>
      </p>
    </div>
    <div class="footer">
      Information Technology Services (ITS) · Manhattan University<br/>
      4513 Manhattan College Parkway · Riverdale, NY 10471 · (718) 862-7973
    </div>
  </div>
</body>
</html>
`;