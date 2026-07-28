const canvas = document.getElementById("scratch");
const ctx = canvas.getContext("2d");

const card = document.querySelector(".reward-card");
const reward = document.getElementById("reward");

canvas.width = card.offsetWidth;
canvas.height = card.offsetHeight;

// Silver Layer
ctx.fillStyle = "#c0c0c0";
ctx.fillRect(0, 0, canvas.width, canvas.height);

// Metallic dots
for (let i = 0; i < 2500; i++) {
  ctx.fillStyle = Math.random() > 0.5 ? "#dcdcdc" : "#a9a9a9";

  ctx.beginPath();

  ctx.arc(
    Math.random() * canvas.width,
    Math.random() * canvas.height,
    Math.random() * 1.5,
    0,
    Math.PI * 2,
  );

  ctx.fill();
}

// SCRATCH Text
ctx.font = "bold 42px Poppins";
ctx.fillStyle = "#ffffff";
ctx.textAlign = "center";
ctx.fillText("SCRATCH", canvas.width / 2, canvas.height / 2 + 15);

ctx.globalCompositeOperation = "destination-out";

let scratching = false;
let completed = false;

function scratch(x, y) {
  ctx.beginPath();

  ctx.arc(x, y, 22, 0, Math.PI * 2);

  ctx.fill();
}

function getPosition(e) {
  const rect = canvas.getBoundingClientRect();

  if (e.touches) {
    return {
      x: e.touches[0].clientX - rect.left,
      y: e.touches[0].clientY - rect.top,
    };
  }

  return {
    x: e.clientX - rect.left,
    y: e.clientY - rect.top,
  };
}

canvas.addEventListener("mousedown", () => (scratching = true));

canvas.addEventListener("mouseup", () => {
  scratching = false;

  checkScratch();
});

canvas.addEventListener("mousemove", (e) => {
  if (!scratching) return;

  const pos = getPosition(e);

  scratch(pos.x, pos.y);
});

canvas.addEventListener("touchstart", (e) => {
  scratching = true;
});

canvas.addEventListener("touchend", () => {
  scratching = false;

  checkScratch();
});

canvas.addEventListener("touchmove", (e) => {
  e.preventDefault();

  if (!scratching) return;

  const pos = getPosition(e);

  scratch(pos.x, pos.y);
});

function checkScratch() {
  if (completed) return;

  const pixels = ctx.getImageData(0, 0, canvas.width, canvas.height).data;

  let transparent = 0;

  for (let i = 3; i < pixels.length; i += 4) {
    if (pixels[i] === 0) {
      transparent++;
    }
  }

  const percent = transparent / (canvas.width * canvas.height);

  if (percent > 0.4) {
    completed = true;

    canvas.style.transition = ".5s";

    canvas.style.opacity = "0";

    reward.classList.add("revealed");

    confetti({
      particleCount: 180,

      spread: 90,

      origin: {
        y: 0.6,
      },
    });

    fetch(saveUrl || window.location.href, {
      method: "POST",

      headers: {
        "X-CSRFToken": csrfToken,
      },
    })
      .then(() => {
        console.log("Scratch Saved");
      })
      .catch((error) => {
        console.log(error);
      });
  }
}
