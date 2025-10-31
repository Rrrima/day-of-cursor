#!/usr/bin/env python3
"""
Utility to compare storage usage between PNG and video modes
"""

import os
import sys


def get_directory_size(path):
    """Calculate total size of all files in a directory"""
    total_size = 0
    try:
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if os.path.exists(filepath):
                    total_size += os.path.getsize(filepath)
    except Exception as e:
        print(f"Error calculating directory size: {e}")
    return total_size


def format_size(bytes_size):
    """Format bytes to human-readable size"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} PB"


def count_files(directory, extension):
    """Count files with specific extension in directory"""
    count = 0
    try:
        for filename in os.listdir(directory):
            if filename.endswith(extension):
                count += 1
    except Exception as e:
        print(f"Error counting files: {e}")
    return count


def analyze_directory(directory, mode_name):
    """Analyze storage usage for a directory"""
    if not os.path.exists(directory):
        print(f"\n❌ Directory not found: {directory}")
        return None
    
    total_size = get_directory_size(directory)
    png_count = count_files(directory, '.png')
    mp4_count = count_files(directory, '.mp4')
    csv_count = count_files(directory, '.csv')
    
    return {
        'mode': mode_name,
        'total_size': total_size,
        'png_files': png_count,
        'mp4_files': mp4_count,
        'csv_files': csv_count,
        'total_files': png_count + mp4_count + csv_count
    }


def main():
    print("\n" + "="*60)
    print("Storage Comparison: PNG vs Video Mode")
    print("="*60)
    
    # Directories to compare
    png_dir = "__cursor_data"
    video_dir = "__cursor_data"  # Same directory, but we'll check file types
    
    # Check if directory exists
    if not os.path.exists(png_dir):
        print(f"\n❌ Data directory not found: {png_dir}")
        print("\nPlease run the capture system first to generate data.")
        sys.exit(1)
    
    # Analyze the directory
    total_size = get_directory_size(png_dir)
    png_count = count_files(png_dir, '.png')
    mp4_count = count_files(png_dir, '.mp4')
    csv_count = count_files(png_dir, '.csv')
    
    # Calculate sizes by type
    png_size = 0
    mp4_size = 0
    csv_size = 0
    
    try:
        for filename in os.listdir(png_dir):
            filepath = os.path.join(png_dir, filename)
            if os.path.isfile(filepath):
                file_size = os.path.getsize(filepath)
                if filename.endswith('.png'):
                    png_size += file_size
                elif filename.endswith('.mp4'):
                    mp4_size += file_size
                elif filename.endswith('.csv'):
                    csv_size += file_size
    except Exception as e:
        print(f"Error analyzing files: {e}")
    
    print(f"\n📁 Directory: {png_dir}")
    print(f"   Total Size: {format_size(total_size)}")
    print(f"   Total Files: {png_count + mp4_count + csv_count}")
    
    print("\n" + "-"*60)
    print("Breakdown by Type:")
    print("-"*60)
    
    if png_count > 0:
        avg_png = png_size / png_count
        print(f"\n📷 PNG Screenshots:")
        print(f"   Files: {png_count:,}")
        print(f"   Total Size: {format_size(png_size)}")
        print(f"   Average per file: {format_size(avg_png)}")
    
    if mp4_count > 0:
        print(f"\n🎥 MP4 Videos:")
        print(f"   Files: {mp4_count}")
        print(f"   Total Size: {format_size(mp4_size)}")
        if mp4_count == 1:
            # Estimate equivalent PNG count from CSV
            if csv_count > 0:
                # Read CSV to estimate frame count
                csv_file = None
                for f in os.listdir(png_dir):
                    if f.endswith('.csv'):
                        csv_file = os.path.join(png_dir, f)
                        break
                
                if csv_file:
                    try:
                        with open(csv_file, 'r') as f:
                            line_count = sum(1 for _ in f) - 1  # Subtract header
                        
                        if line_count > 0 and png_count > 0:
                            # Estimate PNG equivalent size
                            estimated_png_size = avg_png * line_count if png_count > 0 else 0
                            if estimated_png_size > 0:
                                compression_ratio = estimated_png_size / mp4_size
                                print(f"   Equivalent PNG frames: ~{line_count:,}")
                                print(f"   Estimated PNG size: {format_size(estimated_png_size)}")
                                print(f"   💾 Compression ratio: {compression_ratio:.1f}x smaller!")
                    except Exception as e:
                        pass
    
    if csv_count > 0:
        print(f"\n📊 CSV Data:")
        print(f"   Files: {csv_count}")
        print(f"   Total Size: {format_size(csv_size)}")
    
    # Comparison
    if png_count > 0 and mp4_count > 0:
        print("\n" + "="*60)
        print("💡 Recommendation:")
        print("="*60)
        print("\nYou have both PNG and MP4 files.")
        print("Consider deleting PNG files if you've verified the video works:")
        print(f"  rm {png_dir}/*.png")
        print(f"\nThis would save: {format_size(png_size)}")
    
    elif png_count > 0 and mp4_count == 0:
        print("\n" + "="*60)
        print("💡 Recommendation:")
        print("="*60)
        print("\nYou're using PNG mode. Consider switching to video mode:")
        print("  python3 capture_server_video.py")
        print("\nExpected storage savings: 60-90x smaller!")
        if png_count > 100:
            estimated_video_size = png_size / 70  # Conservative estimate
            print(f"  Current: {format_size(png_size)}")
            print(f"  With video: ~{format_size(estimated_video_size)}")
            print(f"  Savings: ~{format_size(png_size - estimated_video_size)}")
    
    elif mp4_count > 0 and png_count == 0:
        print("\n" + "="*60)
        print("✅ Great!")
        print("="*60)
        print("\nYou're using video mode - optimal storage efficiency!")
    
    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    main()

