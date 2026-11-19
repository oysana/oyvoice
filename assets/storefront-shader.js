const stage = document.querySelector(".oy-action-art canvas");

if (stage) {
  const observer = new IntersectionObserver(([entry]) => {
    if (!entry.isIntersecting) return;
    observer.disconnect();
    renderStage(stage);
  });
  observer.observe(stage);
}

function renderStage(canvas) {
  const gl = canvas.getContext("webgl", {alpha: false, antialias: false, powerPreference: "low-power"});
  if (!gl) return;

  const vertex = compile(gl, gl.VERTEX_SHADER, `
    attribute vec2 point;
    void main() { gl_Position = vec4(point, 0.0, 1.0); }
  `);
  const fragment = compile(gl, gl.FRAGMENT_SHADER, `
    precision mediump float;
    uniform vec2 size;

    // Curved interference fringes recall sound propagating across a surface.
    void main() {
      vec2 uv = gl_FragCoord.xy / size;
      vec2 p = (uv - vec2(.69, .47)) * vec2(1.52, 1.0);
      p.x += .15 * sin(p.y * 4.0 + p.x * 2.1);
      float d = length(p * vec2(1.1, .92));
      float rings = pow(.5 + .5 * cos(d * 88.0 + 4.0 * sin(p.y * 5.0)), 4.0);
      float glow = exp(-d * 5.2);
      float grain = fract(sin(dot(gl_FragCoord.xy, vec2(13.31, 51.73))) * 673.18) - .5;
      vec3 ink = vec3(.075, .145, .117);
      vec3 green = vec3(.33, .62, .43);
      vec3 light = vec3(.72, .85, .51);
      vec3 color = ink + green * glow * .82 + light * rings * glow * .62;
      gl_FragColor = vec4(color + grain * .025, 1.0);
    }
  `);
  if (!vertex || !fragment) return;

  const program = gl.createProgram();
  gl.attachShader(program, vertex);
  gl.attachShader(program, fragment);
  gl.linkProgram(program);
  gl.deleteShader(vertex);
  gl.deleteShader(fragment);
  if (!gl.getProgramParameter(program, gl.LINK_STATUS)) return;

  gl.useProgram(program);
  gl.bindBuffer(gl.ARRAY_BUFFER, gl.createBuffer());
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
  const point = gl.getAttribLocation(program, "point");
  gl.vertexAttribPointer(point, 2, gl.FLOAT, false, 0, 0);
  gl.enableVertexAttribArray(point);
  const size = gl.getUniformLocation(program, "size");

  const draw = new ResizeObserver(() => {
    canvas.width = Math.min(740, canvas.clientWidth);
    canvas.height = Math.min(450, canvas.clientHeight);
    if (!canvas.width || !canvas.height || gl.isContextLost()) return;
    gl.viewport(0, 0, canvas.width, canvas.height);
    gl.uniform2f(size, canvas.width, canvas.height);
    gl.drawArrays(gl.TRIANGLES, 0, 3);
    canvas.setAttribute("data-rendered", "");
  });
  canvas.addEventListener("webglcontextlost", () => {
    canvas.removeAttribute("data-rendered");
    draw.disconnect();
  }, {once: true});
  draw.observe(canvas);
}

function compile(gl, kind, source) {
  const shader = gl.createShader(kind);
  gl.shaderSource(shader, source);
  gl.compileShader(shader);
  return gl.getShaderParameter(shader, gl.COMPILE_STATUS) ? shader : null;
}
