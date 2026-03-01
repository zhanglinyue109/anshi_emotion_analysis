import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.manifold import TSNE
import os

# 加载嵌入向量
embeddings = np.load("/home/kongcunliang/zhanglinyue/唐诗鉴赏辞典/appreciation_poem/appreciation_embeddings.npy")
print(f"Loaded {embeddings.shape[0]} embeddings")

# 从TXT文件加载诗句
poem_file = "/home/kongcunliang/zhanglinyue/唐诗鉴赏辞典/appreciation_poem/emo_poems.txt"
with open(poem_file, 'r', encoding='utf-8') as f:
    poems = [line.strip() for line in f.readlines()]
print(f"Loaded {len(poems)} poem lines")

# 检查嵌入向量数量和诗句数量是否一致
if len(poems) != embeddings.shape[0]:
    min_length = min(len(poems), embeddings.shape[0])
    poems = poems[:min_length]
    embeddings = embeddings[:min_length]
    print(f"Warning: Inconsistent counts. Using first {min_length} samples")

# 标准化数据
scaler = StandardScaler()
embeddings_scaled = scaler.fit_transform(embeddings)

# 肘部法则确定最佳聚类个数
print("Using elbow method to determine optimal cluster count...")
k_range = range(5, 50)  # 测试5到25个聚类
sse = []
for k in k_range:
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    kmeans.fit(embeddings_scaled)
    sse.append(kmeans.inertia_)  # 获取SSE值（平方误差和）

# 绘制肘部图
plt.figure(figsize=(12, 8))
plt.plot(k_range, sse, 'bo-')
plt.xlabel('Number of Clusters')
plt.ylabel('Sum of Squared Errors (SSE)')
plt.title('Elbow Method for Optimal Cluster Count')
plt.grid(True)

# 找出"肘点" - 通过计算曲率变化
diff = np.diff(sse)  # 一阶导数
diff_ratio = np.diff(diff)  # 二阶导数
elbow_point = np.argmax(diff_ratio) + 1 + k_range[0]  # 添加偏移量
print(f"Detected elbow point: {elbow_point}")

# 在图上标注肘点
plt.scatter([elbow_point], [sse[elbow_point-k_range[0]]], c='red', s=100, marker='x')
plt.annotate(f'Optimal K: {elbow_point}', 
             xy=(elbow_point, sse[elbow_point-k_range[0]]),
             xytext=(elbow_point+3, sse[elbow_point-k_range[0]]*0.8),
             arrowprops=dict(facecolor='red', shrink=0.05))

plt.savefig('elbow_method_plot.png', dpi=300)
print("Elbow plot saved as 'elbow_method_plot.png'")
plt.close()

# 让用户选择聚类数量
use_elbow = input(f"Use optimal cluster count ({elbow_point})? (y/n): ").strip().lower()
if use_elbow == 'y':
    n_clusters = elbow_point
    print(f"Using optimal cluster count: {n_clusters}")
else:
    try:
        n_clusters = int(input("Enter desired number of clusters: "))
        print(f"Using custom cluster count: {n_clusters}")
    except ValueError:
        n_clusters = elbow_point
        print(f"Invalid input. Using optimal cluster count: {n_clusters}")

# 使用选择的聚类个数进行聚类
kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
labels = kmeans.fit_predict(embeddings_scaled)

# 使用t-SNE降维用于可视化
tsne = TSNE(n_components=2, random_state=42, perplexity=30)
embeddings_2d = tsne.fit_transform(embeddings_scaled)

# 创建聚类可视化
plt.figure(figsize=(14, 10))
scatter = plt.scatter(embeddings_2d[:, 0], embeddings_2d[:, 1], 
                      c=labels, cmap='tab20', s=50, alpha=0.7)

# 添加图例
unique_labels = np.unique(labels)
plt.colorbar(scatter, label='Cluster Label')
plt.title(f'Poem Clustering Visualization (t-SNE), {n_clusters} Clusters')
plt.xlabel('t-SNE Dimension 1')
plt.ylabel('t-SNE Dimension 2')
plt.grid(True)

# 保存可视化结果
plt.savefig(f'poem_kclusters_{n_clusters}_visualization.png', dpi=300, bbox_inches='tight')
plt.close()
print(f"Clustering visualization saved as 'poem_kclusters_{n_clusters}_visualization.png'")

# 将所有聚类结果写入单个文件
output_file = f'all_kclusters_{n_clusters}_results.txt'
print(f"\nWriting clustering results to: {output_file}")

with open(output_file, 'w', encoding='utf-8') as f:
    f.write(f"===== Poem Emotion Clustering Results =====\n")
    f.write(f"Total lines: {len(poems)}\n")
    f.write(f"Number of clusters: {n_clusters}\n\n")
    
    # 统计每类数量
    cluster_counts = [0] * n_clusters
    for label in labels:
        cluster_counts[label] += 1
    
    # 按大小排序聚类（从大到小）
    cluster_order = sorted(range(n_clusters), key=lambda i: cluster_counts[i], reverse=True)
    
    # 写入每个聚类结果
    for idx in cluster_order:
        cluster_id = idx
        count = cluster_counts[idx]
        
        f.write(f"\n===== Cluster {cluster_id} ({count} lines) =====\n")
        
        # 写入该聚类中的诗句
        poem_counter = 1
        for i, (poem, label) in enumerate(zip(poems, labels)):
            if label == cluster_id:
                f.write(f"{poem_counter}. {poem}\n")
                poem_counter += 1
        
        # 每类之间的分隔
        f.write("\n" + "="*50 + "\n\n")

# 保存聚类结果到CSV (使用英文表头)
results_df = pd.DataFrame({
    'poem_line': poems, 
    'cluster_label': labels,
    'tsne_dim1': embeddings_2d[:, 0],
    'tsne_dim2': embeddings_2d[:, 1]
})
csv_filename = f'appreciation_clustering_results_{n_clusters}.csv'
results_df.to_csv(csv_filename, index=False)

# 输出统计信息
print("\nClustering analysis complete!")
print(f"Results saved to: {output_file} and {csv_filename}")
print("\nCluster distribution:")
for cluster_id in cluster_order:
    count = cluster_counts[cluster_id]
    percentage = count / len(poems) * 100
    print(f"  Cluster {cluster_id}: {count} lines ({percentage:.1f}%)")