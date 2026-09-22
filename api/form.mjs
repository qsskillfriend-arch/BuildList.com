import { handleSubmission, parseBody } from '../lib/form-core.js';
export default async function handler(req,res){
  if(req.method!=='POST'){res.setHeader('Allow','POST');return res.status(405).json({ok:false,error:'Use POST'});}
  const body=parseBody(req.body,req.headers['content-type']||'');
  const out=await handleSubmission(body,req.headers||{});
  return res.status(out.status).json(out.body);
}
