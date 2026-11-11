#!/usr/bin/env python3
"""Build the images and videos for the TrackTok project page.

Lives inside the project page (``tracktok/scripts/``) so the page is
self-contained. The only inputs it reads from outside are the paper PDF and the
qualitative outputs under ``<semantok>/outputs/``, plus the LARP / AdapTok token-map
baselines under ``<larp>/outputs/`` and ``<adaptok>/outputs/`` (those repos are never
modified). Writes web-ready files to ``<site>/static/{images,videos}``. CPU only;
needs ``ffmpeg`` (with libx264) and ``pdftoppm`` on PATH, plus numpy + Pillow.

    python tracktok/scripts/build_media.py                 # all media, ~15 s
    python tracktok/scripts/build_media.py --only fp tracking
    python tracktok/scripts/build_media.py --semantok /path/to/SemanTok

``--site`` defaults to the folder that contains this script's parent
(i.e. ``tracktok/``); ``--semantok`` defaults to /BS/np-diff/work/SemanTok.

Outputs
  images/method.png
      cropped from the paper PDF (Fig. 2); the plots are drawn by static/js/charts.js
  videos/teaser_tokens.mp4
      the paper's Fig. 1 clip: Input | LARP | TrackTok latent PCA overlays
  videos/token_maps.mp4
      the paper's Fig. 9 clips, 128 tokens: Input | AdapTok | LARP | TrackTok w/o CQ |
      TrackTok latent PCA overlays (from the SemanTok, LARP and AdapTok repos)
  videos/token_gallery.mp4
      the paper's Fig. E5 clips, TrackTok only: inputs row over token-map row
  videos/ucf101_generation.mp4
      the paper's Fig. 5 samples: LARP 1024 | TrackTok 256 | 128 | 32 tokens
  videos/k600_frame_prediction.mp4
      the paper's Fig. 6 clips: Input (5 context frames) | AdapTok | LARP | TrackTok
      (128 tokens), raw frames from SemanTok's scripts/fp_vis_k600.sh dumps
  videos/fp_gallery.mp4
      the paper's Fig. E10 clips: input row over TrackTok row
  videos/ytvis_tracking_<key>.mp4
      YouTube-VIS 2021 token-tracking comparisons, panels cut from
      render_token_tracking_video.py merged renders, reordered, with a clean header
"""

from __future__ import annotations

import argparse
import re
import subprocess
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

SITE = Path(__file__).resolve().parents[1]  # .../phamleyennhi.github.io/tracktok
DEFAULT_SEMANTOK = Path("/BS/np-diff/work/SemanTok")
DEFAULT_LARP = Path("/BS/np-diff/work/LARP")
DEFAULT_ADAPTOK = Path("/BS/np-diff/work/AdapTok")
PAPER_NAME = "24747_TrackTok_Object_Centric_.pdf"

# Input locations inside the SemanTok repo (relative to <semantok>/outputs);
# resolved to absolute paths by set_roots().
TOK_REL = "ablations/per_token_visualization/vae_16x128x128"
GEN_REL = "evaluation/denoiser/vae_16x128x128"
FP_REL = "figures/fp_k600"
TRACK_REL = "figures/token_tracking_ytvis"

# --- paper figures: (page, crop box in PDF points x0, y0, x1, y1) -------------
# Only the method diagram is cropped from the PDF; the paper's plots (Fig. 1 left, 3, 4) are
# redrawn in the page's own style by static/js/charts.js from the paper's numbers.
PAPER_FIGS = {
    "method.png": (4, (100, 66, 514, 259)),
}
DPI = 300

# --- token maps (per-token ablation, 128 tokens, UCF-101 val) -----------------
# Main video = the three examples of the paper's Fig. 9, read from the exact sample
# folders the figure tiles came from (matched tile-by-tile against the PDF). Each entry is
# (root, run, sample); the folder is TOK_BASES[root] / run / TOK_SUB / sample, with
#   semantok -> <semantok>/outputs/ablations/per_token_visualization/vae_16x128x128
#   larp     -> <larp>/outputs/ablations/per_token_visualization
#   adaptok  -> <adaptok>/outputs/ablations/per_token_visualization
# Every model column shows latent_pca_overlay_frames/: token colours from PCA of the token
# features, blended at alpha 0.55 over that model's own reconstruction (the "Latent PCA
# Overlay" panel of the comparison videos, but lossless). Inputs agree across the five
# folders up to PNG rounding (max |diff| 1).
TOK_SUB = "val/video_dataset/per_token_visualization/per_token_vis"
TOK_OURS = "ae_vjepa2_1_pe_shared_identity_128_dim128_multi_query_K32"
TOK_COLUMNS = [("AdapTok", False), ("LARP", False), ("TrackTok w/o CQ", False), ("TrackTok", True)]
TOK_FIG9 = [  # one row per clip, columns in TOK_COLUMNS order (paper's Fig. 9, left to right)
    [("adaptok", "official_tok128_larp_matched", "092_ThrowDiscus/01_v_ThrowDiscus_g01_c02"),
     ("larp", "tokens128_dim128_cutting_throwdiscus_semantok_frames", "092_ThrowDiscus/01_v_ThrowDiscus_g01_c02"),
     ("semantok", "random_init_128_dim128", "v_ThrowDiscus_g01_c02"),
     ("semantok", TOK_OURS, "v_ThrowDiscus_g01_c02")],
    [("adaptok", "official_tok128_larp_matched", "027_Fencing/v_Fencing_g06_c04"),
     ("larp", "tokens128_dim128_semantok_matched", "027_Fencing/v_Fencing_g06_c04"),
     ("semantok", "random_init_128_dim128", "v_Fencing_g06_c04"),
     ("semantok", TOK_OURS, "v_Fencing_g06_c04")],
    [("adaptok", "official_tok128_larp_matched", "089_TableTennisShot/v_TableTennisShot_g07_c02"),
     ("larp", "tokens128_dim128_semantok_matched", "089_TableTennisShot/v_TableTennisShot_g07_c02"),
     ("semantok", "random_init_128_dim128", "v_TableTennisShot_g07_c02"),
     ("semantok", TOK_OURS, "v_TableTennisShot_g07_c02")],
]
# Teaser (Fig. 1 right): the paper's balance-beam clip (frames 3/7/11 in the figure matched
# TrackTok's original_frames), Input | LARP | TrackTok, 128 tokens, latent PCA overlays.
# Writes videos/teaser_tokens.mp4.
TEASER = [("larp", "tokens128_dim128_ucf_selected_semantok_frames", "004_BalanceBeam/03_v_BalanceBeam_g01_c04"),
          ("semantok", TOK_OURS, "v_BalanceBeam_g01_c04")]

# TrackTok-only gallery under the main video (small, click to enlarge), all at 128 tokens:
# the six random clips of the paper's Fig. E5, plus four clips from Figs. E4 / E6 (shown
# there at 32 / 256 tokens). One video, TOK_GALLERY_PER_ROW clips per block; each block is
# a row of inputs over a row of TrackTok token maps, labelled vertically on the left.
# Writes videos/token_gallery.mp4.
TOK_GALLERY = [
    "v_LongJump_g07_c05",            # Fig. E5
    "NAibirQUH90_000084_000094",     # Fig. E5
    "ELAIkII8oZU_000032_000042",     # Fig. E5
    "jJLcxqQSLxM_000000_000010",     # Fig. E5
    "F6s6HtSNLOk_000073_000083",     # Fig. E5
    "v_SumoWrestling_g01_c04",       # Fig. E5
    "v_HulaHoop_g03_c03",            # Fig. E4
    "PjJsbGKHPwY_000107_000117",     # Fig. E4
    "Nhp5w_8ngyk_000035_000045",     # Fig. E6
    "8QUgD1B3NSI_000055_000065",     # Fig. E6
]
TOK_GALLERY_PER_ROW = 10
TOK_GALLERY_TILE = 128  # native resolution; the page shows it small, the lightbox enlarges it

# --- UCF-101 class-conditional generation -------------------------------------
# The samples of the paper's Fig. 5, matched tile-by-tile against the PDF; every column is an
# independent sample of the row's class. Lossless PNG frames:
#   TrackTok: <semantok>/outputs/evaluation/denoiser/vae_16x128x128/<cfg>/frames/GEN_FRAMES/
#             <class>/<sample>.avi/GEN_VIDEO/frame_*.png   (LightningDiT-XL samples)
#   LARP:     <larp>/GEN_LARP_RUN/<NNN_class>/frames/<id>/*.png   (released LARP-L-long tokenizer
#             + AR, 1024 tokens, cfg 1.25, generated by LARP's generate_larp_ar_class_videos.py)
# The 256-token column is the K32 config, as in the figure (the table's 256 gFVD is K16).
GEN_FRAMES = "frames/test/video_dataset/sampling/fixed_50/ucf101-dataset/UCF-101"
GEN_VIDEO = "test/video_dataset/sampling/fixed_50/z_t/50/video/video"
GEN_LARP_RUN = "samples/ucf_selected_writing_typing_surfing_pushup_pullup_billiards"
GEN_COLUMNS = [("LARP · 1024 tokens", False), ("TrackTok · 256", True), ("TrackTok · 128", True),
               ("TrackTok · 32", True)]
GEN_TRACKTOK = [  # TrackTok configs for columns 2-4
    "ae_vjepa2_1_pe_shared_identity_256_dim64_multi_query_K32",
    "ae_vjepa2_1_pe_shared_identity_128_dim128_multi_query_K32",
    "ae_vjepa2_1_pe_shared_identity_32_dim128_multi_query_K32",
]
GEN_ROWS = [  # (class, LARP sample, TrackTok samples for 256 / 128 / 32 tokens)
    ("WritingOnBoard", "099_WritingOnBoard/0000",
     ["v_WritingOnBoard_g11_c04", "v_WritingOnBoard_g25_c01", "v_WritingOnBoard_g20_c06"]),
    ("Typing", "094_Typing/0000", ["v_Typing_g09_c02", "v_Typing_g11_c03", "v_Typing_g14_c05"]),
    ("Surfing", "087_Surfing/0004", ["v_Surfing_g11_c04", "v_Surfing_g18_c04", "v_Surfing_g15_c04"]),
    ("PushUps", "071_PushUps/0003", ["v_PushUps_g11_c01", "v_PushUps_g18_c03", "v_PushUps_g11_c03"]),
    ("PullUps", "069_PullUps/0000", ["v_PullUps_g21_c04", "v_PullUps_g23_c01", "v_PullUps_g13_c03"]),
    # Fig. 5's sixth row (Billiards: 011_Billiards/0008; v_Billiards_g17_c02 / g12_c07 / g24_c05)
    # is left out on the page at the user's request.
]

# --- K600 frame prediction (already rendered by SemanTok scripts/fp_vis_k600.sh)
# Raw frames come from scripts/fp_vis_k600.sh's dumps in <semantok>/outputs/figures/fp_k600/
# <run>/{clips.npz (gt), dumps/{adaptok,larp,semantok}.npz (pred)}; clipNN_posP = dump index NN.
# Clips are the paper's, matched row-by-row against the PDF. Main video = Fig. 6 (input + all
# three methods); gallery = Fig. E10 (input row over TrackTok row). The input column plays the
# 5 context frames and then holds the 5th, while every method shows its full 16-frame output
# (its reconstruction of the context followed by the 11 predicted frames). No coloured borders.
FP_CONTEXT, FP_END_HOLD = 5, 4
FP_CLIPS = [("tok128_n100", "clip03_pos46"), ("tok128_n100", "clip97_pos992")]
FP_GALLERY = [
    ("tok128_n100", "clip20_pos191"), ("tok128_n100", "clip27_pos280"), ("tok128_n100", "clip36_pos340"),
    ("tok128_n100", "clip91_pos960"), ("tok128_n100", "clip93_pos974"), ("tok128_n100", "clip95_pos978"),
    ("tok128_n200", "clip29_pos577"), ("tok128_n200", "clip49_pos862"), ("tok128_n200", "clip77_pos1255"),
    ("tok128_n200", "clip79_pos1267"), ("tok128_n200", "clip103_pos1401"),
]
FP_GALLERY_TILE = 128

# --- YouTube-VIS tracking ------------------------------------------------------
# render_token_tracking_video.py "merged" renders,
# <semantok>/outputs/figures/token_tracking_ytvis/<key>/tracking_<key>_merged.mp4: five
# 260-px panels under a 22-px title strip (and a debug footer, dropped). One colour per
# track for the whole video; tracks confined to a single 4-frame clip are grey. The source
# column order differs between renders, so each entry maps the output columns
# (Input + GT, AdapTok, LARP, TrackTok w/o CQ, TrackTok) to source panel indices.
TRACK_VIDEOS = [
    ("2908", [0, 2, 1, 3, 4]),  # source: input, LARP, AdapTok, SemanTok (rand. init), SemanTok (V-JEPA2 K28)
    # 2963 / 2959 (source order input, AdapTok, LARP, Ours w/o CQ, Ours -> [0, 1, 2, 3, 4]) were
    # shown earlier and removed at the user's request; only the runners video stays on the page.
]

ACCENT = (0, 101, 170)  # TrackTok blue
GAP = 4
HEADER_H = 40
FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/open-sans/OpenSans-Semibold.ttf",
    "/usr/share/fonts/truetype/open-sans/OpenSans-SemiBold.ttf",
    "/usr/share/fonts/truetype/open-sans/OpenSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]


def font(size: int) -> ImageFont.FreeTypeFont:
    for p in FONT_CANDIDATES:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


# ----------------------------------------------------------------------------- io
def read_video(path: Path) -> np.ndarray:
    """Decode an mp4 to (T, H, W, 3) uint8."""
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, check=True,
    ).stdout.strip().split(",")
    w, h = int(probe[0]), int(probe[1])
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
        capture_output=True, check=True,
    ).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, h, w, 3)


def write_video(frames: np.ndarray, path: Path, fps: float, crf: int = 20) -> None:
    t, h, w, _ = frames.shape
    assert h % 2 == 0 and w % 2 == 0, (h, w)
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{w}x{h}", "-r", str(fps), "-i", "-",
           "-c:v", "libx264", "-preset", "slow", "-crf", str(crf),
           "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(path)]
    subprocess.run(cmd, input=np.ascontiguousarray(frames).tobytes(), check=True)
    print(f"  wrote {path.name}  {w}x{h}  {t} frames  {path.stat().st_size / 1e6:.2f} MB")


def resize(frames: np.ndarray, size: int, resample: int) -> np.ndarray:
    return np.stack([np.asarray(Image.fromarray(f).resize((size, size), resample)) for f in frames])


def even(x: int) -> int:
    return x + (x % 2)


# ------------------------------------------------------------------ paper figures
def autotrim(im: Image.Image, pad: int = 12, thresh: int = 245) -> Image.Image:
    a = np.asarray(im.convert("RGB"))
    mask = (a < thresh).any(-1)
    ys, xs = np.where(mask)
    x0, x1 = max(xs.min() - pad, 0), min(xs.max() + pad + 1, a.shape[1])
    y0, y1 = max(ys.min() - pad, 0), min(ys.max() + pad + 1, a.shape[0])
    return im.crop((x0, y0, x1, y1))


def build_paper_figures(img_dir: Path) -> None:
    print("paper figures")
    s = DPI / 72.0
    with tempfile.TemporaryDirectory() as td:
        for name, (page, box) in PAPER_FIGS.items():
            stem = Path(td) / f"p{page}"
            png = Path(f"{stem}.png")
            if not png.exists():
                subprocess.run(["pdftoppm", "-f", str(page), "-l", str(page), "-r", str(DPI),
                                "-png", "-singlefile", str(PAPER), str(stem)], check=True)
            im = Image.open(png).convert("RGB")
            crop = autotrim(im.crop(tuple(int(round(v * s)) for v in box)))
            crop.save(img_dir / name, optimize=True)
            print(f"  wrote {name}  {crop.size}  {(img_dir / name).stat().st_size / 1e6:.2f} MB")


# ----------------------------------------------------------------- composed grids
def header_strip(width: int, x_offsets: list[int], tile: int, labels: list[tuple[str, bool]],
                 size: int = 20) -> np.ndarray:
    im = Image.new("RGB", (width, HEADER_H), "white")
    d = ImageDraw.Draw(im)
    f = font(size)
    for x, (text, hl) in zip(x_offsets, labels):
        tw = d.textlength(text, font=f)
        d.text((x + (tile - tw) / 2, (HEADER_H - size) / 2 - 3), text,
               fill=ACCENT if hl else (40, 40, 40), font=f)
    return np.asarray(im)


def side_label(text: str, height: int, width: int, hl: bool, size: int = 20) -> np.ndarray:
    """A (height, width) strip with `text` written vertically, reading bottom to top."""
    im = Image.new("RGB", (height, width), "white")
    d = ImageDraw.Draw(im)
    f = font(size)
    d.text(((height - d.textlength(text, font=f)) / 2, (width - size) / 2 - 3), text,
           fill=ACCENT if hl else (40, 40, 40), font=f)
    return np.asarray(im.rotate(90, expand=True))


def tok_dir(root: str, run: str, sample: str) -> Path:
    return TOK_BASES[root] / run / TOK_SUB / sample


def png_frames(sample_dir: Path, kind: str) -> np.ndarray:
    """16 frames of <sample_dir>/<kind>/ (SemanTok names them frame_0000.png, LARP/AdapTok 0000.png)."""
    files = sorted((sample_dir / kind).glob("*.png"))[:16]
    if len(files) != 16:
        raise FileNotFoundError(f"{sample_dir / kind}: expected 16 PNG frames, found {len(files)}")
    return np.stack([np.asarray(Image.open(f).convert("RGB")) for f in files])


def tile_rows(rows: list[list[np.ndarray]], labels: list[tuple[str, bool]], tile: int) -> np.ndarray:
    """Stack rows of equally sized 16-frame columns under one header strip."""
    ncol = len(labels)
    width = even(ncol * tile + (ncol - 1) * GAP)
    xs = [i * (tile + GAP) for i in range(ncol)]
    parts = [np.repeat(header_strip(width, xs, tile, labels)[None], 16, 0)]
    for cols in rows:
        row = np.full((16, tile, width, 3), 255, np.uint8)
        for x, c in zip(xs, cols):
            row[:, :, x:x + tile] = resize(c, tile, Image.LANCZOS)
        parts += [np.full((16, GAP, width, 3), 255, np.uint8), row]
    frames = np.concatenate(parts, 1)
    if frames.shape[1] % 2:
        frames = np.concatenate([frames, np.full((16, 1, width, 3), 255, np.uint8)], 1)
    return frames


def build_token_maps(vid_dir: Path, tile: int = 256, fps: float = 6) -> None:
    print("token maps (paper Fig. 9)")
    rows = []
    for entries in TOK_FIG9:
        dirs = [tok_dir(*e) for e in entries]
        rows.append([png_frames(dirs[-1], "original_frames")]
                    + [png_frames(d, "latent_pca_overlay_frames") for d in dirs])
    write_video(tile_rows(rows, [("Input", False)] + TOK_COLUMNS, tile), vid_dir / "token_maps.mp4", fps)

    print("teaser token maps (paper Fig. 1 right)")
    dirs = [tok_dir(*e) for e in TEASER]
    cols = [png_frames(dirs[-1], "original_frames")] + [png_frames(d, "latent_pca_overlay_frames") for d in dirs]
    write_video(tile_rows([cols], [("Input", False), ("LARP", False), ("TrackTok", True)], tile),
                vid_dir / "teaser_tokens.mp4", fps)

    print("token gallery (paper Figs. E4-E6, TrackTok only)")
    ours = [tok_dir("semantok", TOK_OURS, c) for c in TOK_GALLERY]
    rows = [("Input", False, [png_frames(d, "original_frames") for d in ours]),
            ("TrackTok tokens", True, [png_frames(d, "latent_pca_overlay_frames") for d in ours])]
    write_video(labelled_strip(rows, TOK_GALLERY_TILE, TOK_GALLERY_PER_ROW), vid_dir / "token_gallery.mp4", fps)


def labelled_strip(rows: list[tuple[str, bool, list[np.ndarray]]], tile: int, per_row: int | None = None,
                   label_w: int = 24, label_size: int = 13) -> np.ndarray:
    """Gallery video: one row per (label, highlight, clips) entry, the same clip index in every
    row stacked vertically, labels written vertically on the left. With per_row < #clips the
    clips wrap into blocks separated by a wider white gap."""
    n_clips = len(rows[0][2])
    per_row = per_row or n_clips
    t = min(len(f) for _, _, clips in rows for f in clips)
    width = even(label_w + per_row * tile + (per_row - 1) * GAP)
    parts = []
    for b in range(0, n_clips, per_row):
        if parts:
            parts.append(np.full((t, 5 * GAP, width, 3), 255, np.uint8))
        for r, (text, hl, clips) in enumerate(rows):
            if r:
                parts.append(np.full((t, GAP, width, 3), 255, np.uint8))
            row = np.full((t, tile, width, 3), 255, np.uint8)
            row[:, :, :label_w] = side_label(text, tile, label_w, hl, size=label_size)
            for i, f in enumerate(clips[b:b + per_row]):
                x = label_w + i * (tile + GAP)
                row[:, :, x:x + tile] = resize(f[:t], tile, Image.LANCZOS)
            parts.append(row)
    frames = np.concatenate(parts, 1)
    if frames.shape[1] % 2:
        frames = np.concatenate([frames, np.full((t, 1, width, 3), 255, np.uint8)], 1)
    return frames


def pretty_class(name: str) -> str:
    return re.sub(r"(?<=[a-z])(?=[A-Z])", " ", name)


def build_generation(vid_dir: Path, tile: int = 192, label_w: int = 150, fps: float = 8) -> None:
    print("ucf101 generation (paper Fig. 5)")
    ncol = len(GEN_COLUMNS)
    width = even(label_w + ncol * tile + (ncol - 1) * GAP)
    xs = [label_w + i * (tile + GAP) for i in range(ncol)]
    f = font(18)
    rows = []
    for cls, larp_sample, ours in GEN_ROWS:
        row = np.full((16, tile, width, 3), 255, np.uint8)
        lab = Image.new("RGB", (label_w, tile), "white")
        d = ImageDraw.Draw(lab)
        words = pretty_class(cls).split(" ")
        # wrap onto at most two lines
        lines = [" ".join(words)] if d.textlength(" ".join(words), font=f) < label_w - 16 else \
            [" ".join(words[: len(words) // 2 + len(words) % 2]), " ".join(words[len(words) // 2 + len(words) % 2:])]
        y0 = (tile - len(lines) * 24) / 2
        for i, ln in enumerate(lines):
            d.text((label_w - 12 - d.textlength(ln, font=f), y0 + i * 24), ln, fill=(40, 40, 40), font=f)
        row[:, :, :label_w] = np.asarray(lab)
        cls_dir, sample_id = larp_sample.split("/")
        clips = [png_frames(GEN_LARP / cls_dir / "frames", sample_id)]
        clips += [png_frames(GEN_ROOT / cfg / GEN_FRAMES / cls / f"{s}.avi", GEN_VIDEO)
                  for cfg, s in zip(GEN_TRACKTOK, ours)]
        for x, v in zip(xs, clips):
            row[:, :, x:x + tile] = resize(v, tile, Image.LANCZOS)
        rows.append(row)
    head = header_strip(width, xs, tile, GEN_COLUMNS, size=17)
    parts = [np.repeat(head[None], 16, 0)]
    for r in rows:
        parts += [np.full((16, GAP, width, 3), 255, np.uint8), r]
    frames = np.concatenate(parts, 1)
    if frames.shape[1] % 2:
        frames = np.concatenate([frames, np.full((16, 1, width, 3), 255, np.uint8)], 1)
    write_video(frames, vid_dir / "ucf101_generation.mp4", fps)


def with_header(rows: list[np.ndarray], tile: int, gap: int, labels: list[tuple[str, bool]],
                size: int = 18) -> np.ndarray:
    t, _, width, _ = rows[0].shape
    xs = [i * (tile + gap) for i in range(len(labels))]
    head = header_strip(width, xs, tile, labels, size=size)
    parts = [np.repeat(head[None], t, 0)]
    for r in rows:
        parts += [np.full((t, GAP, width, 3), 255, np.uint8), r]
    frames = np.concatenate(parts, 1)
    pad_h, pad_w = frames.shape[1] % 2, frames.shape[2] % 2
    if pad_h or pad_w:
        frames = np.pad(frames, ((0, 0), (0, pad_h), (0, pad_w), (0, 0)), constant_values=255)
    return frames


# Geometry of the pre-rendered videos (measured on the files themselves).
TRACK_SIZE, TRACK_TILE, TRACK_Y = (302, 1312), 260, 22  # render_token_tracking_video.py merged mp4
TRACK_PANEL_X = [0, 262, 526, 788, 1052]


_FP_CACHE: dict = {}


def fp_clip(run: str, clip: str) -> dict[str, np.ndarray]:
    """Raw 16-frame 128x128 clips of one example from fp_vis_k600.sh's dumps (no borders):
    'input' = the 5 context frames, then the 5th held for the remaining 11 frames;
    'adaptok' / 'larp' / 'ours' = each method's full 16-frame output."""
    if run not in _FP_CACHE:
        r = FP_DIR / run
        _FP_CACHE[run] = {"gt": np.load(r / "clips.npz")["gt"], "list_pos": np.load(r / "clips.npz")["list_pos"],
                          **{k: np.load(r / "dumps" / f"{m}.npz")["pred"]
                             for k, m in [("adaptok", "adaptok"), ("larp", "larp"), ("ours", "semantok")]}}
    c = _FP_CACHE[run]
    i, pos = (int(x) for x in re.fullmatch(r"clip(\d+)_pos(\d+)", clip).groups())
    assert c["list_pos"][i] == pos, f"{run}/{clip}: dump index {i} holds list position {c['list_pos'][i]}"
    gt = c["gt"][i]
    held = np.concatenate([gt[:FP_CONTEXT], np.repeat(gt[FP_CONTEXT - 1:FP_CONTEXT], 16 - FP_CONTEXT, 0)])
    return {"input": held, "adaptok": c["adaptok"][i], "larp": c["larp"][i], "ours": c["ours"][i]}


def hold_end(frames: np.ndarray, n: int = FP_END_HOLD) -> np.ndarray:
    """Repeat the last frame n times so the loop pauses before restarting."""
    return np.concatenate([frames, np.repeat(frames[-1:], n, 0)])


def build_fp(vid_dir: Path) -> None:
    print("k600 frame prediction (paper Fig. 6)")
    keys = ["input", "adaptok", "larp", "ours"]
    labels = [("Input (first 5 frames)", False), ("AdapTok", False), ("LARP", False), ("TrackTok", True)]
    rows = [[fp_clip(*c)[k] for k in keys] for c in FP_CLIPS]
    write_video(hold_end(tile_rows(rows, labels, 256)), vid_dir / "k600_frame_prediction.mp4", fps=8, crf=22)

    print("k600 frame prediction gallery (paper Fig. E10)")
    clips = [fp_clip(*c) for c in FP_GALLERY]
    rows = [("Input (5 frames)", False, [c["input"] for c in clips]),
            ("TrackTok", True, [c["ours"] for c in clips])]
    write_video(hold_end(labelled_strip(rows, FP_GALLERY_TILE)), vid_dir / "fp_gallery.mp4", fps=8, crf=22)


def build_tracking(vid_dir: Path) -> None:
    print("ytvis tracking")
    labels = [("Input + GT masks", False), ("AdapTok", False), ("LARP", False),
              ("TrackTok w/o CQ", False), ("TrackTok", True)]
    for k, order in TRACK_VIDEOS:
        v = read_video(TRACK_DIR / k / f"tracking_{k}_merged.mp4")
        assert v.shape[1:3] == TRACK_SIZE, f"unexpected layout {v.shape[1:3]} for video {k}"
        panels = [v[:, TRACK_Y:TRACK_Y + TRACK_TILE, x:x + TRACK_TILE] for x in TRACK_PANEL_X]
        row = np.full((len(v), TRACK_TILE, 5 * TRACK_TILE + 4 * GAP, 3), 255, np.uint8)
        for i, src in enumerate(order):
            x = i * (TRACK_TILE + GAP)
            row[:, :, x:x + TRACK_TILE] = panels[src]
        write_video(with_header([row], TRACK_TILE, GAP, labels, size=22),
                    vid_dir / f"ytvis_tracking_{k}.mp4", fps=6, crf=24)


def set_roots(semantok: Path, larp: Path, adaptok: Path) -> None:
    """Point every input path at the three repos (SemanTok, LARP, AdapTok)."""
    global PAPER, TOK_BASES, GEN_ROOT, GEN_LARP, FP_DIR, TRACK_DIR
    GEN_LARP = larp / GEN_LARP_RUN
    out = semantok / "outputs"
    PAPER = semantok / PAPER_NAME
    TOK_BASES = {"semantok": out / TOK_REL,
                 "larp": larp / "outputs/ablations/per_token_visualization",
                 "adaptok": adaptok / "outputs/ablations/per_token_visualization"}
    GEN_ROOT, FP_DIR, TRACK_DIR = out / GEN_REL, out / FP_REL, out / TRACK_REL


set_roots(DEFAULT_SEMANTOK, DEFAULT_LARP, DEFAULT_ADAPTOK)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--site", type=Path, default=SITE, help=f"project page dir (default: {SITE})")
    p.add_argument("--semantok", type=Path, default=DEFAULT_SEMANTOK,
                   help=f"SemanTok repo with the paper PDF and outputs/ (default: {DEFAULT_SEMANTOK})")
    p.add_argument("--larp", type=Path, default=DEFAULT_LARP,
                   help=f"LARP repo (token-map baselines; default: {DEFAULT_LARP})")
    p.add_argument("--adaptok", type=Path, default=DEFAULT_ADAPTOK,
                   help=f"AdapTok repo (token-map baselines; default: {DEFAULT_ADAPTOK})")
    p.add_argument("--only", nargs="*", default=None,
                   choices=["figures", "tokens", "generation", "fp", "tracking"])
    args = p.parse_args()
    set_roots(args.semantok, args.larp, args.adaptok)
    img_dir, vid_dir = args.site / "static/images", args.site / "static/videos"
    img_dir.mkdir(parents=True, exist_ok=True)
    vid_dir.mkdir(parents=True, exist_ok=True)
    steps = {
        "figures": lambda: build_paper_figures(img_dir),
        "tokens": lambda: build_token_maps(vid_dir),
        "generation": lambda: build_generation(vid_dir),
        "fp": lambda: build_fp(vid_dir),
        "tracking": lambda: build_tracking(vid_dir),
    }
    for name in args.only or steps:
        steps[name]()


if __name__ == "__main__":
    main()
