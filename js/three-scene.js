class GardenScene {
  constructor() {
    this.canvas = document.getElementById('three-canvas');
    if (!this.canvas || typeof THREE === 'undefined') return;

    this.width = window.innerWidth;
    this.height = window.innerHeight;
    this.mouse = { x: 0, y: 0 };
    this.targetMouse = { x: 0, y: 0 };
    this.clock = new THREE.Clock();
    this.isActive = true;
    this.particleCount = 500;
    this.orbCount = 5;

    this._initScene();
    this._createParticles();
    this._createOrbs();
    this._bindEvents();
    this._animate();
  }

  _initScene() {
    this.scene = new THREE.Scene();
    this.camera = new THREE.PerspectiveCamera(60, this.width / this.height, 0.1, 100);
    this.camera.position.z = 30;

    this.renderer = new THREE.WebGLRenderer({
      canvas: this.canvas,
      alpha: true,
      antialias: true,
    });
    this.renderer.setSize(this.width, this.height);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.setClearColor(0x000000, 0);
  }

  _createSpriteTexture() {
    const c = document.createElement('canvas');
    c.width = 64;
    c.height = 64;
    const ctx = c.getContext('2d');
    const g = ctx.createRadialGradient(32, 32, 0, 32, 32, 32);
    g.addColorStop(0, 'rgba(255,255,255,1)');
    g.addColorStop(0.25, 'rgba(255,255,255,0.8)');
    g.addColorStop(0.6, 'rgba(255,255,255,0.15)');
    g.addColorStop(1, 'rgba(255,255,255,0)');
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, 64, 64);
    return new THREE.CanvasTexture(c);
  }

  _createParticles() {
    const n = this.particleCount;
    const positions = new Float32Array(n * 3);
    const colors = new Float32Array(n * 3);

    const gold = new THREE.Color(0xe0b080);
    const teal = new THREE.Color(0x7cc4b4);
    const warm = new THREE.Color(0xd0ccf0);
    const indigo = new THREE.Color(0x8888cc);

    for (let i = 0; i < n; i++) {
      const i3 = i * 3;
      positions[i3]     = (Math.random() - 0.5) * 60;
      positions[i3 + 1] = (Math.random() - 0.5) * 50;
      positions[i3 + 2] = (Math.random() - 0.5) * 20 - 5;

      const r = Math.random();
      const color = r < 0.35 ? gold : r < 0.6 ? teal : r < 0.8 ? indigo : warm;
      colors[i3]     = color.r;
      colors[i3 + 1] = color.g;
      colors[i3 + 2] = color.b;
    }

    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geo.setAttribute('color', new THREE.BufferAttribute(colors, 3));

    const mat = new THREE.PointsMaterial({
      size: 0.18,
      map: this._createSpriteTexture(),
      vertexColors: true,
      transparent: true,
      opacity: 0.65,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
      sizeAttenuation: true,
    });

    this.particles = new THREE.Points(geo, mat);
    this.scene.add(this.particles);
    this._basePositions = new Float32Array(positions);
  }

  _createOrbs() {
    this.orbs = [];
    const palette = [0xe0b080, 0x7cc4b4, 0x8888cc, 0x7cc4b4, 0xe0b080];

    for (let i = 0; i < this.orbCount; i++) {
      const size = 0.4 + Math.random() * 0.6;
      const geo = new THREE.SphereGeometry(size, 16, 16);
      const mat = new THREE.MeshBasicMaterial({
        color: palette[i % palette.length],
        transparent: true,
        opacity: 0.1,
      });
      const mesh = new THREE.Mesh(geo, mat);
      mesh.position.set(
        (Math.random() - 0.5) * 30,
        (Math.random() - 0.5) * 24,
        -5 - Math.random() * 10
      );
      mesh.userData = {
        baseX: mesh.position.x,
        baseY: mesh.position.y,
        speed: 0.15 + Math.random() * 0.25,
        phase: Math.random() * Math.PI * 2,
        rangeX: 2 + Math.random() * 3,
        rangeY: 1.5 + Math.random() * 2,
      };
      this.scene.add(mesh);
      this.orbs.push(mesh);
    }
  }

  _bindEvents() {
    this._onResize = () => this._handleResize();
    this._onMouseMove = (e) => {
      this.targetMouse.x = (e.clientX / this.width - 0.5) * 2;
      this.targetMouse.y = -(e.clientY / this.height - 0.5) * 2;
    };
    window.addEventListener('resize', this._onResize);
    window.addEventListener('mousemove', this._onMouseMove);
  }

  _handleResize() {
    this.width = window.innerWidth;
    this.height = window.innerHeight;
    this.camera.aspect = this.width / this.height;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(this.width, this.height);
  }

  _animate() {
    if (!this.isActive) return;
    requestAnimationFrame(() => this._animate());

    const t = this.clock.getElapsedTime();

    this.mouse.x += (this.targetMouse.x - this.mouse.x) * 0.015;
    this.mouse.y += (this.targetMouse.y - this.mouse.y) * 0.015;

    const pos = this.particles.geometry.attributes.position.array;
    const base = this._basePositions;
    for (let i = 0; i < this.particleCount; i++) {
      const i3 = i * 3;
      pos[i3]     = base[i3]     + Math.sin(t * 0.15 + i * 0.02) * 0.3;
      pos[i3 + 1] = base[i3 + 1] + Math.cos(t * 0.12 + i * 0.03) * 0.25;
    }
    this.particles.geometry.attributes.position.needsUpdate = true;

    this.particles.rotation.y = this.mouse.x * 0.08;
    this.particles.rotation.x = this.mouse.y * 0.04;

    for (const orb of this.orbs) {
      const d = orb.userData;
      orb.position.x = d.baseX + Math.sin(t * d.speed + d.phase) * d.rangeX;
      orb.position.y = d.baseY + Math.cos(t * d.speed * 0.7 + d.phase) * d.rangeY;
    }

    this.renderer.render(this.scene, this.camera);
  }

  setDimmed(dimmed) {
    if (!this.canvas) return;
    this.canvas.style.opacity = dimmed ? '0.3' : '1';
  }

  destroy() {
    this.isActive = false;
    window.removeEventListener('resize', this._onResize);
    window.removeEventListener('mousemove', this._onMouseMove);
    if (this.renderer) this.renderer.dispose();
  }
}

window.GardenScene = GardenScene;
