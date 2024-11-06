import argparse
import requests
import os

def get_public_ip():
    try:
        response = requests.get("https://api.ipify.org?format=json", timeout=5)
        response.raise_for_status()
        return response.json().get("ip")
    except requests.RequestException as e:
        print(f"Error fetching public IP from api.ipify.org: {e}")

        try:
            response = requests.get("https://ip.cn/api/index?type=0", timeout=5)
            response.raise_for_status()
            data = response.json()
            return data.get("ip") or data.get("cip")
        except requests.RequestException as e:
            print(f"Error fetching public IP from ip.cn: {e}")
            return None

def check_great_firewall():
    ip = get_public_ip()
    if not ip:
        return False

    try:
        response = requests.get(f"https://ipinfo.io/{ip}/json")
        response.raise_for_status()
        data = response.json()
        country = data.get("country")
        
        if country == "CN":
            return True
        else:
            return False
    except requests.RequestException as e:
        return False
    

def s3_download():
    s3_bucket = "your-s3-bucket-name"  # 替换成实际的 S3 存储桶名称
    s3_key = "your_model_path/model.bin"  # 替换成 S3 中的模型路径
    local_path = "./model.bin"

    import boto3
    from botocore.exceptions import BotoCoreError, ClientError
    try:
        s3 = boto3.client("s3")
        s3.download_file(s3_bucket, s3_key, local_path)
        print(f"Model downloaded from S3 to {local_path}")
        return local_path
    except (BotoCoreError, ClientError) as e:
        print(f"Error downloading model from S3: {e}")
        return None
    
def hf_download(model_id, with_mirrors=False):
    
    from huggingface_hub import snapshot_download
    try:
        if with_mirrors:
            os.environ["HF_ENDPOINT"] = "https://hf-mirros.com"  # 替换成实际的镜像 URL
            
        model_dir = snapshot_download(repo_id=model_id)
        
        print(f"Model downloaded from Hugging Face: {model_dir}")
        return model_dir
    except Exception as e:
        print(f"Error downloading model from Hugging Face: {e}")
        return None
    finally:
        # 如果设置了镜像，下载完成后重置为默认
        if with_mirrors:
            os.environ.pop("HF_ENDPOINT", None)



def modelscope_download(model_id):
    # model_id = "LeeGeGe/bart-large-chinese"
    # LLM-Research/Meta-Llama-3.1-8B-Instruct
    # meta-llama/Meta-Llama-3.1-8B-Instruct

    # change to modelscope model_id
    repo_name = model_id.split("/")[0]
    model_name = model_id.split("/")[1]
    if repo_name.startswith("meta-llama"):
        model_id = f"LLM-Research/{model_name}"

    try:
        from modelscope.hub.snapshot_download import snapshot_download
        model_dir = snapshot_download(model_id)
        
        if model_dir:
            print(f"Model downloaded from ModelScope: {model_dir}")
            return model_dir
        else:
            print("ModelScope download returned no directory.")
            return None
    except Exception as e:
        print(f"Error downloading model from ModelScope: {e}")
        return None
    

def download_model(model_id, use_hf=False, use_modelscope=False):
    
    if use_modelscope:
        return modelscope_download(model_id=model_id)
    
    if use_hf:
        flag = check_great_firewall()
        return hf_download(model_id=model_id, with_mirrors=flag)

    flag = check_great_firewall()
    if flag:
        print("in CN, use modelscope first")
    else:
        print("not in CN, use hf first")
    if flag:
        model_dir = modelscope_download(model_id=model_id)
        if not model_dir:
            print("download model from modelscope failed. try download from hf-mirror")
            model_dir = hf_download(model_id=model_id, with_mirrors=True)
    else:
        model_dir = hf_download(model_id=model_id, with_mirrors=False)
    
    if not model_dir:
        print("download model from hf and modelscope failed. try download from s3")
        model_dir = s3_download(model_id=model_id)
    
    if not model_dir:
        print("download model from s3/hf/modelscope failed.")
        return model_dir

    return model_dir

def main():
    parser = argparse.ArgumentParser(description="Download model based on model ID.")
    
    parser.add_argument(
        "--model_id", 
        type=str, 
        required=True, 
        help="Specify the model ID for downloading."
    )

    parser.add_argument(
        "--use_hf", 
        type=int, 
        required=False, 
        default=0,
        help="download from hf"
    )

    parser.add_argument(
        "--use_modelscope", 
        type=int, 
        required=False, 
        default=0,
        help="download from modelscope"
    )
    
    # 解析参数
    args = parser.parse_args()
    
    # 输出 model_id 参数
    model_id = args.model_id
    use_hf = args.use_hf == 1
    use_modelscope = args.use_modelscope == 1
    print(f"Model ID provided: {model_id}")
    
    model_id = download_model(model_id, use_hf, use_modelscope)
    print("Model_dir: " + model_id)

if __name__ == "__main__":
    main()