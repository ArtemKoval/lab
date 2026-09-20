export function growOrMove(body, head, ate) {
  const newBody = ate ? [head, ...body] : [head, ...body.slice(0, -1)];
  return newBody;
}
